"""프로젝트 전역 설정.

- 비밀값(API 키 등)은 .env 에서만 읽는다. 코드·로그에 남기지 않는다.
- 모델명·호출 환경·[TBD] 기준 파일 경로는 이 파일 한 곳에서 교체한다.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
REFERENCE_DIR = DATA_DIR / "reference"
SAMPLES_DIR = DATA_DIR / "samples"
PROMPTS_DIR = BASE_DIR / "prompts"
MAIL_TEMPLATES_DIR = BASE_DIR / "app" / "mail" / "templates"

# ---------------------------------------------------------------------------
# DB (SQLite 파일럿 → 추후 PostgreSQL URL 로 교체)
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'esg_pilot.db'}")

# ---------------------------------------------------------------------------
# LLM (모델명은 여기서만 관리)
# ---------------------------------------------------------------------------
# 호출 환경: "anthropic"(직접 API) | 사내 클라우드 경유 등은 추후 추가  [TBD: 보안 검토 결과]
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # .env 전용

MODEL_DEFAULT = os.getenv("MODEL_DEFAULT", "claude-sonnet-5-5")  # 판정·매칭
MODEL_LIGHT = os.getenv("MODEL_LIGHT", "claude-haiku-4-5-20251001")  # 단순 분류·요약

# ---------------------------------------------------------------------------
# 파일럿 운영 원칙
# ---------------------------------------------------------------------------
MAIL_DRY_RUN = True  # 파일럿 기간 실제 발송 금지. outbox 저장만 한다.

# ---------------------------------------------------------------------------
# [TBD] 기준 파일 — 담당자 자료가 오면 파일만 교체
# ---------------------------------------------------------------------------
REFERENCE_FILES = {
    "risk_tier_criteria": REFERENCE_DIR / "risk_tier_criteria.yaml",  # [TBD] 단계 4
    "saq_questions": REFERENCE_DIR / "saq_questions.yaml",  # [TBD] 단계 5
    "scoring_table": REFERENCE_DIR / "scoring_table.yaml",  # [TBD] 단계 5
    "best_practices": REFERENCE_DIR / "best_practices.yaml",  # [TBD] 단계 7
}

# ---------------------------------------------------------------------------
# 샘플 데이터 생성 설정 (단계 1)
# ---------------------------------------------------------------------------
SAMPLE_SUPPLIER_COUNT = 20
SAMPLE_RANDOM_SEED = 42
SAMPLE_DIAGNOSIS_YEAR = 2026
