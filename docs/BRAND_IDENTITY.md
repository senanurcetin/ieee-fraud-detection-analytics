# NEXUS brand identity — Fraud Risk Intelligence

## Approved source

The NEXUS assets are taken from the owner's private Google Drive **Logo / NEXUS_Identity_2_0** identity pack, dated **14 October 2026**. The approved identity is the third Figma concept, with the cyan → blue → lavender → violet signature X. The brand source is private; only approved logo artwork is published in this repository.

No new/reinterpreted logo was generated for Fraud Risk Intelligence. A byte-level comparison of the canonical Git blob IDs confirmed that the repository already contains exact copies of all three official **SVG** exports:

| Identity source file | Repository asset | Verified SHA-256 |
|---|---|---|
| `NEXUS_Official_Midnight_Logo.svg` | `docs/assets/nexus-official-midnight.svg` | `c31c9df29384ea3d75587a757a7b28386e66e41c1b52ce072887df1cbf00d6bd` |
| `NEXUS_Official_Transparent_Logo.svg` | `docs/assets/nexus-official-transparent.svg` | `143788fc114348b03bcef5285c134d63135bd7dbd908380e973596f743c9f45b` |
| `NEXUS_Official_X_Transparent.svg` | `docs/assets/nexus-official-mark.svg` | `62b6f2a3b306b4c969098f92dfb578ef7ca20373b202872782c70ec8e1dd1dbe` |

`webapp/static/seo/favicon.svg` is **byte-identical** to the approved X icon and is the canonical web-serving asset. The original Git objects match the authorized Drive SVG byte content exactly. The SVG contains vector artwork; it is not an external Drive hotlink and does not require a network connection at runtime.

## Actual product usage

- `README.md`: official Midnight wordmark on the project's public GitHub landing page.
- `webapp/static/index.html`: approved X in the left navigation rail instead of the original `NX` text placeholder.
- `webapp/static/decision-studio.html`: the same approved X instead of the original single-letter `N` placeholder.
- `/research`: the approved X and the same NEXUS color family.
- `/`, `/studio` and `/research`: the same X-based favicon served from `/static/seo/favicon.svg`.
- Navigation mark remains decorative (`alt=""`, `aria-hidden="true"`) because adjacent text names the NEXUS application. Explicit width/height avoids layout shift. Color, contrast and focus styling remain in each page's existing stylesheets.

Colors taken from the official source: `#0B0F19`, `#061524`, `#00E0FF`, `#4EA8FF`, `#8F9BFF`, `#6E55C6`, `#B9C5CE`.

## Update procedure

If the owner publishes a new approved NEXUS identity pack, replace the canonical assets as an explicitly reviewed brand update. Recompute source checksums, update the tests and document provenance. Do not replace the vector logo with a mock `N`/`NX`, an AI approximation, an unofficial social banner, or a private Google Drive hotlink. Run Python CI, Docker smoke, native Chromium desktop/mobile checks and public release controls independently. Firefox/WebKit and broader interaction acceptance remain tracked in issue #29; the Playwright workflow stays disabled.

This is **brand integration only**. It does not refresh IEEE-CIS data, recalibrate predictions or verify live BigQuery/production release.
