"""샘플 협력사 20곳을 생성하고 DB 에 적재한다.

사용법 (esg-ax-pilot/ 에서):
    python -m scripts.seed_sample            # 샘플 CSV 가 있으면 그대로 적재
    python -m scripts.seed_sample --regen    # 샘플 CSV 재생성 후 적재
"""
from __future__ import annotations

import argparse

from sqlalchemy import func, select

import config
from app.db.models import Case, Supplier
from app.db.sample_data import generate_suppliers, load_suppliers, read_csv, write_csv
from app.db.session import init_db, make_engine, make_session_factory

SAMPLE_CSV = config.SAMPLES_DIR / "suppliers_sample.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regen", action="store_true", help="샘플 CSV 재생성")
    args = parser.parse_args()

    if args.regen or not SAMPLE_CSV.exists():
        write_csv(generate_suppliers(), SAMPLE_CSV)
        print(f"샘플 CSV 생성: {SAMPLE_CSV}")

    engine = make_engine()
    init_db(engine)
    Session = make_session_factory(engine)
    with Session() as s:
        ns, nc = load_suppliers(s, read_csv(SAMPLE_CSV))
        total_s = s.scalar(select(func.count()).select_from(Supplier))
        total_c = s.scalar(select(func.count()).select_from(Case))
    print(f"신규 협력사 {ns}곳, 신규 케이스 {nc}건 적재 (전체 협력사 {total_s}곳, 케이스 {total_c}건)")


if __name__ == "__main__":
    main()
