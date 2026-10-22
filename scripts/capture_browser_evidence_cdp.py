"""Capture genuine rendered NEXUS pages through native Chromium CDP, without Playwright.

Requires an installed Chromium browser and the optional websocket-client package.
Uses an isolated temporary profile and loopback debugging. Screenshots retain the
browser's original PNG bytes; no overlays, compositing or post-processing occur.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_MARK_SHA256 = "62b6f2a3b306b4c969098f92dfb578ef7ca20373b202872782c70ec8e1dd1dbe"


def read_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def browser_path() -> Path:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Pass --browser with an installed Chromium executable")


class CDP:
    def __init__(self, url: str):
        import websocket

        self.ws = websocket.create_connection(url, timeout=30, suppress_origin=True)
        self.sequence = 0
        self.exceptions: list[str] = []

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.sequence += 1
        self.ws.send(json.dumps({"id": self.sequence, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("method") == "Runtime.exceptionThrown":
                self.exceptions.append(message["params"]["exceptionDetails"].get("text", "JavaScript exception"))
            if message.get("id") == self.sequence:
                if "error" in message:
                    raise RuntimeError(f"CDP command failed: {method}")
                return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in result:
            raise RuntimeError("Browser assertion expression failed")
        return result.get("result", {}).get("value")

    def wait(self, expression: str, timeout: float = 60) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.evaluate(expression):
                return
            time.sleep(0.25)
        raise TimeoutError("Rendered page did not reach required ready state")

    def close(self) -> None:
        self.ws.close()


def capture(
    browser: Path, base_url: str, output: Path, *, expected_sha: str | None = None,
    capture_date: str = "2026-10-22",
) -> dict[str, Any]:
    dt.date.fromisoformat(capture_date)
    stamp = capture_date.replace("-", "")
    output.mkdir(parents=True, exist_ok=True)
    evidence = read_json(base_url + "/api/evidence-status")
    if expected_sha and evidence.get("deployed_git_commit") != expected_sha:
        raise ValueError("Target application revision differs from expected Git SHA")
    with socket.socket() as free_socket:
        free_socket.bind(("127.0.0.1", 0))
        debug_port = free_socket.getsockname()[1]
    # No existing personal browser profile or user tabs are opened or controlled.
    with tempfile.TemporaryDirectory(prefix="nexus-cdp-", ignore_cleanup_errors=True) as profile:
        process = subprocess.Popen(
            [str(browser), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
             "--hide-scrollbars", f"--user-data-dir={profile}", f"--remote-debugging-port={debug_port}",
             "--remote-debugging-address=127.0.0.1", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        client = None
        try:
            target = None
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    target = next(item for item in read_json(f"http://127.0.0.1:{debug_port}/json/list") if item["type"] == "page")
                    break
                except (OSError, StopIteration):
                    time.sleep(0.25)
            if target is None:
                raise TimeoutError("Isolated Chromium debugging target unavailable")
            version = read_json(f"http://127.0.0.1:{debug_port}/json/version")["Browser"]
            client = CDP(target["webSocketDebuggerUrl"])
            client.call("Page.enable")
            client.call("Runtime.enable")
            captures = []
            for name, route, width, height, mobile in [
                (f"nexus_dashboard_desktop_{stamp}.png", "/", 1440, 1000, False),
                (f"nexus_dashboard_mobile_{stamp}.png", "/", 390, 844, True),
                (f"nexus_studio_desktop_{stamp}.png", "/studio?view=overview", 1440, 1000, False),
                (f"nexus_studio_mobile_{stamp}.png", "/studio?view=overview", 390, 844, True),
                (f"nexus_research_desktop_{stamp}.png", "/research", 1440, 1000, False),
                (f"nexus_research_mobile_{stamp}.png", "/research", 390, 844, True),
            ]:
                client.exceptions.clear()
                client.call("Emulation.setDeviceMetricsOverride", {
                    "width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile,
                })
                client.call("Page.navigate", {"url": base_url + route})
                client.wait("document.readyState === 'complete'")
                if route == "/research":
                    client.wait("!document.querySelector('#results').hidden && document.querySelectorAll('#metrics tr').length === 4 && !!document.querySelector('#reliability svg')")
                elif route.startswith("/studio"):
                    client.wait("document.querySelector('#main-content')?.getAttribute('aria-busy') === 'false' && document.querySelector('#metric-grid')?.children.length > 0")
                else:
                    client.wait("document.querySelector('#backend-pill')?.dataset.state === 'connected' && document.querySelector('#state')?.classList.contains('hidden')")
                client.evaluate("document.fonts.ready.then(() => true)")
                client.wait("[...document.querySelectorAll('.brand-symbol')].every(x => x.complete && x.naturalWidth > 0)")
                time.sleep(0.4)
                observation = client.evaluate("""(() => ({
                    title: document.title,
                    horizontal_overflow: document.documentElement.scrollWidth > innerWidth + 1,
                    viewport: [innerWidth, innerHeight],
                    logo_sources: [...document.querySelectorAll('.brand-symbol')].map(x => new URL(x.src).pathname),
                    historical_disclosure: /historical/i.test(document.body.innerText),
                    metric_count: document.querySelector('#metric-grid')?.children.length ?? document.querySelectorAll('.kpi-card').length,
                    font_family: getComputedStyle(document.body).fontFamily
                }))()""")
                if observation["horizontal_overflow"] or not observation["historical_disclosure"]:
                    raise AssertionError(f"Rendered contract failed for {name}: {observation}")
                if observation["logo_sources"] != ["/static/seo/favicon.svg"] or client.exceptions:
                    raise AssertionError(f"Official-logo/JavaScript contract failed for {name}")
                raw_png = base64.b64decode(client.call("Page.captureScreenshot", {
                    "format": "png", "captureBeyondViewport": False, "fromSurface": True,
                })["data"])
                (output / name).write_bytes(raw_png)
                interactions = []
                if route.startswith("/studio"):
                    for tab in ["performance", "governance", "brief"]:
                        client.evaluate(f"document.querySelector('#tab-{tab}').click()")
                        client.wait(f"document.querySelector('#tab-{tab}').getAttribute('aria-selected') === 'true' && !document.querySelector('#panel-{tab}').hidden")
                        interactions.append(f"{tab} tab selects and reveals corresponding panel")
                elif route == "/" and not mobile:
                    pages = client.evaluate("[...document.querySelectorAll('.nav-btn[data-page]')].map(x=>x.dataset.page)")
                    if len(pages) != 9:
                        raise AssertionError("Expected nine historical reporting pages")
                    for page in pages:
                        key = json.dumps(page)
                        client.evaluate(f"[...document.querySelectorAll('.nav-btn')].find(x=>x.dataset.page==={key}).click()")
                        client.wait(f"document.querySelector('.nav-btn[aria-current=page]')?.dataset.page === {key}")
                        interactions.append(f"Historical report page {page} selects successfully")
                    before = client.evaluate("document.body.classList.contains('light')")
                    client.evaluate("document.querySelector('#theme-btn').click()")
                    if client.evaluate("document.body.classList.contains('light')") == before:
                        raise AssertionError("Theme control did not change presentation")
                    client.evaluate("document.querySelector('#theme-btn').click()")
                    interactions.append("Light/dark theme control toggles and restores original state")
                if client.exceptions:
                    raise AssertionError(f"JavaScript exception during interactions on {route}")
                captures.append({
                    "asset": str((output / name).relative_to(ROOT)).replace("\\", "/"),
                    "source_url": base_url + route, "pixel_size": [width, height],
                    "sha256": hashlib.sha256(raw_png).hexdigest(), "observations": observation,
                    "javascript_exceptions": client.exceptions.copy(), "interactions": interactions,
                })
            logo_bytes = urllib.request.urlopen(base_url + "/static/seo/favicon.svg", timeout=20).read()
            if hashlib.sha256(logo_bytes).hexdigest() != OFFICIAL_MARK_SHA256:
                raise AssertionError("Served logo differs from approved NEXUS X")
            return {
                "captured_at_utc": dt.datetime.now(dt.UTC).isoformat(),
                "client_date": capture_date, "browser": version,
                "capture_method": "Native Chromium Chrome DevTools Protocol; no Playwright; unedited viewport PNG bytes",
                "browser_profile": "Isolated temporary profile; loopback debugging; best-effort cleanup after process-tree termination",
                "observed_deployed_git_commit": evidence.get("deployed_git_commit"),
                "historical_source_as_of": evidence.get("source_as_of"),
                "served_official_mark_sha256": OFFICIAL_MARK_SHA256,
                "status": "PASS_NATIVE_CHROMIUM_PRESENTATION_CONTRACT", "files": captures,
                "scope": "Chromium desktop/mobile dashboard, Studio and research; nine-page selection, theme and Studio tabs. Not Firefox/WebKit or prospective model validation.",
                "source_text_sha256_lf_normalized": {
                    str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
                    for path in sorted((ROOT / "webapp").rglob("*"))
                    if path.is_file() and path.suffix in {".html", ".css", ".js", ".py"}
                },
            }
        finally:
            if client is not None:
                client.close()
            if os.name == "nt" and process.poll() is None:
                # Stop only the browser tree created above, including Crashpad,
                # before removing its isolated temporary profile on Windows.
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                )
            elif process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            time.sleep(0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--base-url", default="https://fraud-project-web.vercel.app")
    parser.add_argument("--expected-sha")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/assets")
    parser.add_argument("--capture-date", default=dt.datetime.now().date().isoformat())
    args = parser.parse_args()
    report = capture(args.browser or browser_path(), args.base_url.rstrip("/"), args.output_dir.resolve(), expected_sha=args.expected_sha, capture_date=args.capture_date)
    target = args.output_dir / ("native_browser_provenance_" + args.capture_date.replace("-", "") + ".json")
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "screenshots": len(report["files"]), "provenance": str(target)}))


if __name__ == "__main__":
    main()
