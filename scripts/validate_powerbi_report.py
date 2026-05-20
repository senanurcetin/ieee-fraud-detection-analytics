from __future__ import annotations

import json
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PBIX = ROOT / "powerbi" / "fraud_project_v2.pbix"

SAFE_FIELDS = {
    "mart_fraud_summary": {
        "total_transactions",
        "fraud_transactions",
        "fraud_rate",
        "identity_coverage_rate",
    },
    "fact_train_transactions": {
        "product_cd",
        "risk_band",
        "card_network",
        "card_type",
        "amount_band",
        "purchaser_email_group",
        "is_fraud",
        "transaction_amount",
        "transaction_hour",
        "device_type",
    },
    "mart_risk_band_stats": {"risk_band", "observed_fraud_rate"},
    "mart_feature_missingness": {"column_family", "column_name", "missing_rate", "missing_count", "row_count"},
}

SAFE_VISUAL_TYPES = {"textbox", "slicer", "clusteredColumnChart", "clusteredBarChart", "tableEx"}
RAW_LABEL_MARKERS = {
    "product_cd",
    "fraud_rate",
    "observed_fraud_rate",
    "is_fraud",
    "transaction_amount",
    "risk_band",
    "amount_band",
    "purchaser_email_group",
    "device_type",
    "card_network",
    "card_type",
}


def literal_is_true(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    literal_value = value.get("expr", {}).get("Literal", {}).get("Value")
    return literal_value == "true"


def textbox_runs(visual: dict) -> list[tuple[str, float]]:
    runs: list[tuple[str, float]] = []
    for general in visual.get("objects", {}).get("general", []):
        properties = general.get("properties", {})
        for paragraph in properties.get("paragraphs", []):
            for run in paragraph.get("textRuns", []):
                text = str(run.get("value", ""))
                font_raw = str(run.get("textStyle", {}).get("fontSize", "10pt")).replace("pt", "")
                try:
                    font_size = float(font_raw)
                except ValueError:
                    font_size = 10.0
                runs.append((text, font_size))
    return runs


def column_refs(obj: object, aliases: dict[str, str], refs: list[tuple[str, str]]) -> None:
    if isinstance(obj, dict):
        column = obj.get("Column")
        if isinstance(column, dict):
            alias = column.get("Expression", {}).get("SourceRef", {}).get("Source")
            table = aliases.get(alias)
            prop = column.get("Property")
            if table and prop:
                refs.append((table, prop))
        for value in obj.values():
            column_refs(value, aliases, refs)
    elif isinstance(obj, list):
        for item in obj:
            column_refs(item, aliases, refs)


def main() -> int:
    if not PBIX.exists():
        print(f"PBIX not found: {PBIX}")
        return 1

    with ZipFile(PBIX) as zf:
        layout = json.loads(zf.read("Report/Layout").decode("utf-16le"))
        names = zf.namelist()
        zip_test = zf.testzip()

        visual_types: dict[str, int] = {}
        raw_query_refs: list[tuple[str, str | None, str]] = []
        field_violations: list[tuple[str, str | None, str, str]] = []
        native_title_violations: list[tuple[str, str | None, str]] = []
        clipped_text_risks: list[tuple[str, str | None, str]] = []
        tooltip_visuals = 0
        query_bound_visuals = 0

        for section in layout["sections"]:
            for container in section.get("visualContainers", []):
                config = json.loads(container.get("config", "{}"))
                visual = config.get("singleVisual", {})
                visual_type = visual.get("visualType")
                visual_types[visual_type] = visual_types.get(visual_type, 0) + 1

                if visual_type != "textbox":
                    for title_object in visual.get("objects", {}).get("title", []):
                        if literal_is_true(title_object.get("properties", {}).get("show")):
                            native_title_violations.append(
                                (section["displayName"], config.get("name"), str(visual_type))
                            )

                if visual_type == "textbox":
                    position = config.get("layouts", [{}])[0].get("position", {})
                    width = float(position.get("width", container.get("width", 0)) or 0)
                    height = float(position.get("height", container.get("height", 0)) or 0)
                    for text, font_size in textbox_runs(visual):
                        cleaned = " ".join(text.split())
                        if not cleaned:
                            continue
                        if cleaned in {"■"}:
                            continue
                        estimated_single_line_width = len(cleaned) * font_size * 0.43
                        needs_wrap = estimated_single_line_width > width
                        min_height = font_size * (2.8 if needs_wrap else 1.55)
                        if height < min_height:
                            clipped_text_risks.append((section["displayName"], config.get("name"), cleaned[:80]))

                projections = visual.get("projections", {})
                if projections:
                    query_bound_visuals += 1
                if "Tooltips" in projections:
                    tooltip_visuals += 1
                for items in projections.values():
                    for item in items:
                        query_ref = item.get("queryRef", "")
                        if any(marker in query_ref for marker in RAW_LABEL_MARKERS):
                            raw_query_refs.append((section["displayName"], config.get("name"), query_ref))

                query = visual.get("prototypeQuery") or {}
                aliases = {item.get("Name"): item.get("Entity") for item in query.get("From", [])}
                refs: list[tuple[str, str]] = []
                column_refs(query, aliases, refs)
                for table, field in refs:
                    if field not in SAFE_FIELDS.get(table, set()):
                        field_violations.append((section["displayName"], visual_type, table, field))

        checks = {
            "zip_integrity": zip_test is None,
            "six_pages": len(layout["sections"]) == 6,
            "safe_visual_types": not (set(visual_types) - SAFE_VISUAL_TYPES),
            "no_png_resources": not any(
                name.startswith("Report/StaticResources/RegisteredResources/") and name.lower().endswith(".png")
                for name in names
            ),
            "no_security_bindings": "SecurityBindings" not in names,
            "no_field_violations": not field_violations,
            "no_raw_query_refs": not raw_query_refs,
            "no_native_card_visuals": visual_types.get("card", 0) == 0,
            "native_titles_disabled": not native_title_violations,
            "no_clipped_text_risk": not clipped_text_risks,
            "min_query_visuals": query_bound_visuals >= 27,
            "min_tooltip_visuals": tooltip_visuals >= 12,
        }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"visual_types: {visual_types}")
    print(f"query_bound_visuals: {query_bound_visuals}")
    print(f"tooltip_visuals: {tooltip_visuals}")
    print(f"raw_query_refs: {len(raw_query_refs)}")
    print(f"field_violations: {len(field_violations)}")
    print(f"native_title_violations: {len(native_title_violations)}")
    print(f"clipped_text_risks: {len(clipped_text_risks)}")

    if not all(checks.values()):
        if raw_query_refs:
            print(f"raw_query_ref_examples: {raw_query_refs[:5]}")
        if field_violations:
            print(f"field_violation_examples: {field_violations[:5]}")
        if native_title_violations:
            print(f"native_title_violation_examples: {native_title_violations[:5]}")
        if clipped_text_risks:
            print(f"clipped_text_risk_examples: {clipped_text_risks[:5]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
