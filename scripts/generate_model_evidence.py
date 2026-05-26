"""Recompute model validation evidence from exported validation artifacts.

The script is intentionally lightweight: it does not retrain the model. It reads
the validation predictions exported by ``src/prepare_raw_and_ml.py`` and writes a
portfolio-ready markdown evidence file that can be reviewed independently.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_fscore_support, roc_auc_score

REPO_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = REPO_ROOT / "outputs" / "tables"
OUTPUT_DOC = REPO_ROOT / "docs" / "model_validation_recomputed.md"


def pct(value: float) -> str:
    return f"{value:.2%}"


def num(value: float) -> str:
    return f"{value:,.4f}"


def load_predictions() -> pd.DataFrame:
    path = TABLES_DIR / "validation_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(
            "Missing outputs/tables/validation_predictions.csv. "
            "Run `python src/prepare_raw_and_ml.py` first."
        )
    frame = pd.read_csv(path)
    expected = {"actual", "prediction"}
    missing = expected.difference(frame.columns)
    if missing:
        raise ValueError(f"Validation prediction file is missing required columns: {sorted(missing)}")
    return frame.dropna(subset=["actual", "prediction"]).copy()


def load_feature_importance() -> pd.DataFrame:
    path = TABLES_DIR / "feature_importance.csv"
    if not path.exists():
        return pd.DataFrame(columns=["feature", "importance", "feature_family"])
    return pd.read_csv(path)


def compute_metrics(predictions: pd.DataFrame) -> dict[str, float]:
    actual = predictions["actual"].astype(int)
    score = predictions["prediction"].astype(float)
    threshold = float(score.quantile(0.95))
    predicted = (score >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        actual,
        predicted,
        average="binary",
        zero_division=0,
    )
    true_negative = int(((actual == 0) & (predicted == 0)).sum())
    false_positive = int(((actual == 0) & (predicted == 1)).sum())
    false_positive_rate = false_positive / max(false_positive + true_negative, 1)
    baseline = float(actual.mean())
    top_decile_threshold = float(score.quantile(0.90))
    top_decile_rate = float(actual[score >= top_decile_threshold].mean())
    return {
        "validation_rows": float(len(predictions)),
        "fraud_baseline": baseline,
        "roc_auc": float(roc_auc_score(actual, score)),
        "average_precision": float(average_precision_score(actual, score)),
        "operating_threshold": threshold,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": float(false_positive_rate),
        "workload_share": float(predicted.mean()),
        "top_decile_lift": float(top_decile_rate / baseline) if baseline else 0.0,
    }


def calibration_table(predictions: pd.DataFrame) -> pd.DataFrame:
    frame = predictions.copy()
    frame["score_decile"] = pd.qcut(frame["prediction"], 10, labels=False, duplicates="drop") + 1
    grouped = (
        frame.groupby("score_decile", as_index=False)
        .agg(
            transaction_count=("actual", "size"),
            avg_score=("prediction", "mean"),
            observed_fraud_rate=("actual", "mean"),
        )
        .sort_values("score_decile")
    )
    grouped["calibration_gap"] = grouped["observed_fraud_rate"] - grouped["avg_score"]
    return grouped


def feature_family_table(feature_importance: pd.DataFrame) -> pd.DataFrame:
    if feature_importance.empty:
        return feature_importance
    return (
        feature_importance.groupby("feature_family", as_index=False)
        .agg(
            feature_count=("feature", "count"),
            total_importance=("importance", "sum"),
            top_feature=("feature", lambda values: values.iloc[0]),
        )
        .sort_values("total_importance", ascending=False)
    )


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def build_document(metrics: dict[str, float], calibration: pd.DataFrame, family: pd.DataFrame) -> str:
    metric_rows = [
        ["Validation rows", f"{int(metrics['validation_rows']):,}", "Time-based holdout population."],
        ["Validation fraud baseline", pct(metrics["fraud_baseline"]), "Base precision before model ranking."],
        ["ROC-AUC", num(metrics["roc_auc"]), "Ranking power across thresholds."],
        ["Average precision", num(metrics["average_precision"]), "Imbalance-aware model quality."],
        ["Top decile lift", f"{metrics['top_decile_lift']:.2f}x", "Fraud concentration in the highest-score decile."],
        ["Operating threshold", num(metrics["operating_threshold"]), "p95 validation score threshold."],
        ["Precision at threshold", pct(metrics["precision"]), "Reviewed transactions that are fraud."],
        ["Recall at threshold", pct(metrics["recall"]), "Fraud labels captured by the queue."],
        ["False-positive rate", pct(metrics["false_positive_rate"]), "Legitimate transactions sent to review."],
        ["Workload share", pct(metrics["workload_share"]), "Share of validation transactions reviewed."],
    ]
    calibration_rows = [
        [
            str(int(row.score_decile)),
            f"{int(row.transaction_count):,}",
            pct(row.avg_score),
            pct(row.observed_fraud_rate),
            pct(row.calibration_gap),
        ]
        for row in calibration.itertuples()
    ]
    family_rows = [
        [
            str(row.feature_family),
            f"{int(row.feature_count):,}",
            f"{int(row.total_importance):,}",
            str(row.top_feature),
        ]
        for row in family.head(10).itertuples()
    ]
    return "\n\n".join(
        [
            "# Recomputed Model Validation Evidence",
            "This file is generated from exported validation artifacts and can be recreated with `python scripts/generate_model_evidence.py`.",
            "## Validation Metrics",
            markdown_table(metric_rows, ["Metric", "Value", "Interpretation"]),
            "## Calibration by Score Decile",
            markdown_table(calibration_rows, ["Score decile", "Rows", "Average score", "Observed fraud rate", "Calibration gap"]),
            "## Feature Family Evidence",
            markdown_table(family_rows, ["Feature family", "Feature count", "Total importance", "Top feature"]),
            "## Governance Note",
            "The model is suitable for prioritizing analyst review queues. It should not be used as an autonomous decline engine without calibrated probabilities, production decision logs, and bank-specific cost validation.",
        ]
    ) + "\n"


def main() -> None:
    predictions = load_predictions()
    feature_importance = load_feature_importance()
    metrics = compute_metrics(predictions)
    document = build_document(metrics, calibration_table(predictions), feature_family_table(feature_importance))
    OUTPUT_DOC.write_text(document, encoding="utf-8")
    print(f"Wrote {OUTPUT_DOC.relative_to(REPO_ROOT)}")
    print(f"ROC-AUC={metrics['roc_auc']:.4f} AveragePrecision={metrics['average_precision']:.4f}")


if __name__ == "__main__":
    main()
