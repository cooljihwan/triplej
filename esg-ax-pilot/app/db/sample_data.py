"""샘플 협력사 데이터 생성·적재 (단계 1).

실제 Click ESG 내보내기 파일이 오기 전까지 쓰는 익명화 샘플이다.
같은 seed 로는 항상 같은 데이터가 나온다.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from app.db.models import Case, CaseStatus, Supplier

INDUSTRIES = ["전자부품", "화학", "금속가공", "섬유", "물류", "플라스틱사출", "배터리소재", "IT서비스"]
COUNTRIES = ["KR", "KR", "KR", "CN", "VN", "IN", "MX", "US", "DE"]  # 국내 비중을 높게
TRANSACTION_TYPES = ["직접재", "간접재", "외주가공", "서비스"]

CSV_FIELDS = [
    "supplier_id",
    "name",
    "industry",
    "country",
    "transaction_amount",
    "transaction_type",
    "contact_email",
]


def generate_suppliers(n: int = config.SAMPLE_SUPPLIER_COUNT, seed: int = config.SAMPLE_RANDOM_SEED) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        sid = f"S{i:03d}"
        rows.append(
            {
                "supplier_id": sid,
                "name": f"협력사-{i:03d}",  # 익명화
                "industry": rng.choice(INDUSTRIES),
                "country": rng.choice(COUNTRIES),
                # 연간 거래규모(백만원): 로그 분포 느낌으로 소/중/대 섞기
                "transaction_amount": int(rng.choice([1, 5, 20, 80]) * rng.uniform(50, 250)),
                "transaction_type": rng.choice(TRANSACTION_TYPES),
                "contact_email": f"contact+{sid.lower()}@example.com",  # 마스킹
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["transaction_amount"] = int(r["transaction_amount"])
    return rows


def load_suppliers(
    session: Session,
    rows: list[dict],
    diagnosis_year: int = config.SAMPLE_DIAGNOSIS_YEAR,
    saq_due_date: date | None = None,
) -> tuple[int, int]:
    """협력사와 진단 케이스(IMPORTED)를 적재한다. 이미 있으면 건너뛴다.

    반환: (신규 협력사 수, 신규 케이스 수)
    """
    saq_due_date = saq_due_date or date(diagnosis_year, 1, 1) + timedelta(days=300)
    existing_suppliers = set(session.scalars(select(Supplier.supplier_id)))
    existing_cases = {
        (sid, year) for sid, year in session.execute(select(Case.supplier_id, Case.diagnosis_year))
    }

    new_suppliers = new_cases = 0
    for r in rows:
        sid = r["supplier_id"]
        if sid not in existing_suppliers:
            session.add(Supplier(**{k: r[k] for k in CSV_FIELDS}))
            new_suppliers += 1
        if (sid, diagnosis_year) not in existing_cases:
            session.add(
                Case(
                    case_id=f"C{diagnosis_year}-{sid}",
                    supplier_id=sid,
                    diagnosis_year=diagnosis_year,
                    status=CaseStatus.IMPORTED,
                    saq_due_date=saq_due_date,
                )
            )
            new_cases += 1
    session.commit()
    return new_suppliers, new_cases
