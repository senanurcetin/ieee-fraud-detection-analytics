"""Full public-contract transforms and read bounds, without credentials or network."""
from datetime import UTC, datetime
from types import SimpleNamespace

import duckdb
import pytest

from scripts.verify_reporting_full_parity_readonly import (
    FACT_FIELDS,
    MAX_FACT_ROWS,
    floating_aggregation_residuals,
    mirror_table,
    public_query_rows,
)


def test_filters_are_not_mistaken_for_full_tables() -> None:
    with duckdb.connect(":memory:") as conn:
        conn.execute("create table rpt_model_risk_bands (split varchar, risk_band varchar, band_rank int)")
        conn.execute("insert into rpt_model_risk_bands values ('train','critical',1),('validation','low',2)")
        bands = public_query_rows(conn, "model_risk_bands")
        assert len(bands) == 1 and bands[0]["split"] == "train"
        conn.execute("create table rpt_feature_importance (feature varchar, feature_family varchar, importance float, importance_rank int)")
        conn.execute("insert into rpt_feature_importance values ('keep','V',0.9,15),('exclude','V',0.8,16)")
        assert [row["feature"] for row in public_query_rows(conn, "feature_importance")] == ["keep"]


def test_quality_scorecard_uses_exact_family_aggregation() -> None:
    with duckdb.connect(":memory:") as conn:
        conn.execute("create table rpt_data_quality_scorecard (column_family varchar, column_count int, avg_missing_rate double, max_missing_rate double, total_missing_values int, row_count int)")
        conn.execute("insert into rpt_data_quality_scorecard values ('V',2,0.2,0.3,20,100),('V',3,0.4,0.8,40,100)")
        result = public_query_rows(conn, "data_quality")
        assert len(result) == 1
        assert result[0]["column_count"] == 5
        assert result[0]["avg_missing_rate"] == pytest.approx(0.3)
        assert result[0]["max_missing_rate"] == 0.8
        assert result[0]["total_missing_values"] == 60
        assert result[0]["row_count"] == 100


def create_fact(conn) -> None:
    columns = [f'"{name}" ' + ("double" if name == "transaction_amount" else "int" if name in {"has_identity", "is_fraud"} else "varchar") for name in FACT_FIELDS]
    conn.execute("create table fact_train_transactions (" + ",".join(columns) + ")")


def test_all_four_fact_aggregates_handle_nulls_and_preserve_counts() -> None:
    with duckdb.connect(":memory:") as conn:
        create_fact(conn)
        record = {name: None for name in FACT_FIELDS}
        record.update(has_identity=0, is_fraud=1, transaction_amount=12.5)
        conn.executemany("insert into fact_train_transactions values (" + ",".join("?" for _ in FACT_FIELDS) + ")", [[record[name] for name in FACT_FIELDS]] * 1000)
        payment = public_query_rows(conn, "payment_email_matrix")
        assert payment == [{"payment_segment": "Unknown / Unknown", "email_segment": "Unknown", "transaction_count": 1000, "fraud_count": 1000, "fraud_rate": 1.0, "avg_transaction_amount": 12.5}]
        product = public_query_rows(conn, "proxy_product_matrix")
        assert len(product) == 2 and all(row["transaction_count"] == 1000 for row in product)
        assert {row["proxy_family"] for row in product} == {"Address proxy", "Distance proxy"}
        cross = public_query_rows(conn, "proxy_cross_matrix")
        assert cross[0]["fraud_count"] == 1000 and cross[0]["fraud_rate"] == 1
        niche = public_query_rows(conn, "niche_drilldown")
        assert len(niche) == 42
        assert all(row["transaction_count"] == 1000 and row["fraud_transaction_amount"] == 12500 for row in niche)
        assert all(row["parent_family"] != row["child_family"] for row in niche)


def test_payment_minimum_support_is_applied() -> None:
    with duckdb.connect(":memory:") as conn:
        create_fact(conn)
        conn.execute("insert into fact_train_transactions (is_fraud, transaction_amount) values (0,5)")
        assert public_query_rows(conn, "payment_email_matrix") == []


class FakeSource:
    def __init__(self, count=2, changed=False):
        self.count = count
        self.changed = changed
        self.metadata_reads = 0
        self.row_reads = 0
        self.schema = [SimpleNamespace(name="value", field_type="STRING", mode="NULLABLE")]

    def get_table(self, ref, *, timeout):
        self.metadata_reads += 1
        return SimpleNamespace(num_rows=self.count, schema=self.schema, modified=datetime(2026, 1, 1, tzinfo=UTC), etag="changed" if self.changed and self.metadata_reads > 1 else "original")

    def list_rows(self, info, *, selected_fields, max_results, page_size, timeout):
        self.row_reads += 1
        assert max_results == self.count + 1 and page_size == 10000
        return SimpleNamespace(pages=[[{"value": None}, {"value": "present"}]])


def test_mirror_preserves_null_string_schema_and_never_writes_raw_files() -> None:
    with duckdb.connect(":memory:") as conn:
        source = FakeSource()
        evidence = mirror_table(source, conn, "test.table", fact=False)
        assert evidence["rows_read"] == 2
        assert conn.execute("select count(*) from \"table\" where value is null").fetchone()[0] == 1
        assert len(evidence["selected_row_multiset_sha256_sum_mod_2_256"]) == 64
        assert "present" not in str(evidence)


@pytest.mark.parametrize("count,fact", [(10001, False), (MAX_FACT_ROWS + 1, True), (MAX_FACT_ROWS - 1, True)])
def test_source_bounds_fail_before_row_download(count, fact) -> None:
    with duckdb.connect(":memory:") as conn:
        source = FakeSource(count=count)
        with pytest.raises(ValueError):
            mirror_table(source, conn, "test.table", fact=fact)
        assert source.row_reads == 0


def test_mutating_or_incomplete_sources_fail_closed() -> None:
    for source in (FakeSource(count=3), FakeSource(changed=True)):
        with duckdb.connect(":memory:") as conn, pytest.raises(ValueError):
            mirror_table(source, conn, "test.table", fact=False)


def test_float_rounding_boundary_diagnostic_does_not_hide_real_changes():
    row = {"parent_family": "Product", "parent_segment": "A", "child_family": "Payment",
           "child_segment": "B", "transaction_count": 1000, "avg_transaction_amount": 12.3456784999999}
    current = {**row, "avg_transaction_amount": 12.3456785000001}
    diagnostic = floating_aggregation_residuals("niche_drilldown", [row], [current])
    assert diagnostic is not None and diagnostic["maximum_absolute_residual"] < 1e-9
    for change in ({"transaction_count": 1001}, {"child_segment": "changed"},
                   {"avg_transaction_amount": 12.3457}, {"avg_transaction_amount": None}):
        assert floating_aggregation_residuals("niche_drilldown", [row], [{**row, **change}]) is None
    assert floating_aggregation_residuals("niche_drilldown", [row, row], [current, current]) is None
