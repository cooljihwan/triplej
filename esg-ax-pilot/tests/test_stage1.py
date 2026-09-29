"""단계 1 완료 기준: 샘플 협력사 20곳이 DB 에 적재됨."""
import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

import config
from app.db.models import Case, CaseStatus, Finding, Supplier, Verdict
from app.db.sample_data import generate_suppliers, load_suppliers, read_csv, write_csv

EXPECTED_TABLES = {
    "suppliers", "cases", "saq_responses", "evidence_files", "findings", "scores",
    "improvement_items", "best_practices", "outbox", "approvals", "surveys",
    "audit_log", "llm_usage",
}


def test_all_spec_tables_created(session):
    assert EXPECTED_TABLES <= set(inspect(session.get_bind()).get_table_names())


def test_sample_generation_is_deterministic():
    assert generate_suppliers() == generate_suppliers()
    assert len(generate_suppliers()) == 20


def test_sample_is_anonymized():
    for r in generate_suppliers():
        assert r["name"].startswith("협력사-")
        assert r["contact_email"].endswith("@example.com")


def test_load_20_suppliers_as_imported(session):
    ns, nc = load_suppliers(session, generate_suppliers())
    assert (ns, nc) == (20, 20)
    assert session.scalar(select(func.count()).select_from(Supplier)) == 20
    statuses = set(session.scalars(select(Case.status)))
    assert statuses == {CaseStatus.IMPORTED}


def test_load_is_idempotent(session):
    rows = generate_suppliers()
    load_suppliers(session, rows)
    assert load_suppliers(session, rows) == (0, 0)
    assert session.scalar(select(func.count()).select_from(Case)) == 20


def test_csv_roundtrip(tmp_path):
    rows = generate_suppliers()
    path = tmp_path / "s.csv"
    write_csv(rows, path)
    assert read_csv(path) == rows


def test_committed_sample_csv_matches_generator():
    path = config.SAMPLES_DIR / "suppliers_sample.csv"
    assert path.exists(), "python -m scripts.seed_sample --regen 으로 생성"
    assert read_csv(path) == generate_suppliers()


def test_foreign_key_enforced(session):
    session.add(Case(case_id="X", supplier_id="NOPE", diagnosis_year=2026))
    with pytest.raises(IntegrityError):
        session.commit()


def test_verdict_stored_as_korean_label(session):
    load_suppliers(session, generate_suppliers()[:1])
    session.add(Finding(case_id="C2026-S001", question_id="E-03", verdict=Verdict.MISMATCH,
                        evidence={"file": "a.pdf", "page": 1, "summary": "x"}, created_by="test"))
    session.commit()
    raw = session.connection().exec_driver_sql("SELECT verdict FROM findings").scalar()
    assert raw == "불일치"
