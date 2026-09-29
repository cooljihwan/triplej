"""DB 모델 (SPEC 5장).

SQLite 파일럿용이지만 PostgreSQL 전환을 고려해 SQLAlchemy 표준 타입만 사용하고,
Enum 은 문자열(VARCHAR)로 저장한다(native_enum=False).
"""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum(e: type[enum.Enum]) -> Enum:
    return Enum(e, native_enum=False, length=40, values_callable=lambda x: [m.value for m in x])


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------
class CaseStatus(str, enum.Enum):
    """SPEC 4장 상태 머신. 전이 규칙은 단계 3(app/workflow)에서 구현."""

    IMPORTED = "IMPORTED"
    TIER_PENDING_APPROVAL = "TIER_PENDING_APPROVAL"
    SAQ_REQUESTED = "SAQ_REQUESTED"
    SAQ_RECEIVED = "SAQ_RECEIVED"
    SCREENING_PENDING_APPROVAL = "SCREENING_PENDING_APPROVAL"
    DIAGNOSIS_CONFIRMED = "DIAGNOSIS_CONFIRMED"
    IMPROVEMENT_PENDING_APPROVAL = "IMPROVEMENT_PENDING_APPROVAL"
    MONITORING = "MONITORING"
    SURVEY = "SURVEY"
    CLOSED = "CLOSED"


class RiskTier(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EsgArea(str, enum.Enum):
    E = "E"
    S = "S"
    G = "G"


class Verdict(str, enum.Enum):
    CONFORM = "적합"
    MISMATCH = "불일치"
    MISSING_EVIDENCE = "증빙누락"
    NEEDS_REVIEW = "확인필요"


class Priority(str, enum.Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"


class OutboxStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "승인"
    REJECTED = "반려"


class ActorType(str, enum.Enum):
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))  # 익명화 가능
    industry: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    transaction_amount: Mapped[int] = mapped_column(Integer)  # 연간 거래규모(백만원)
    transaction_type: Mapped[str] = mapped_column(String(50))
    contact_email: Mapped[str | None] = mapped_column(String(200))  # 마스킹된 값
    # [TBD: Click ESG 컬럼 매핑] 매핑되지 않은 원본 컬럼 보존용
    extra: Mapped[dict | None] = mapped_column(JSON)

    cases: Mapped[list[Case]] = relationship(back_populates="supplier")


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (UniqueConstraint("supplier_id", "diagnosis_year"),)

    case_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.supplier_id"))
    diagnosis_year: Mapped[int] = mapped_column(Integer)
    status: Mapped[CaseStatus] = mapped_column(_enum(CaseStatus), default=CaseStatus.IMPORTED)
    risk_tier: Mapped[RiskTier | None] = mapped_column(_enum(RiskTier))
    saq_due_date: Mapped[date | None] = mapped_column(Date)  # 자가진단 응답 기한 (운영 Agent 현황 점검용)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    supplier: Mapped[Supplier] = relationship(back_populates="cases")


class SaqResponse(Base):
    __tablename__ = "saq_responses"
    __table_args__ = (UniqueConstraint("case_id", "question_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    question_id: Mapped[str] = mapped_column(String(20))
    area: Mapped[EsgArea] = mapped_column(_enum(EsgArea))
    answer: Mapped[str | None] = mapped_column(Text)
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=False)


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    question_id: Mapped[str] = mapped_column(String(20))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))
    issued_date: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    question_id: Mapped[str] = mapped_column(String(20))
    verdict: Mapped[Verdict] = mapped_column(_enum(Verdict))
    # 근거: {"file": ..., "page": ..., "summary": ...} — 근거 없는 판정은 저장하지 않는다 (단계 5에서 검증)
    evidence: Mapped[dict] = mapped_column(JSON)
    comment: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_by: Mapped[str] = mapped_column(String(50))  # 생성 Agent
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (UniqueConstraint("case_id", "indicator_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    indicator_id: Mapped[str] = mapped_column(String(20))
    score: Mapped[float] = mapped_column(Float)
    basis: Mapped[dict | None] = mapped_column(JSON)  # 코드 계산 근거


class ImprovementItem(Base):
    __tablename__ = "improvement_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    indicator_id: Mapped[str] = mapped_column(String(20))
    issue: Mapped[str] = mapped_column(Text)
    bp_ids: Mapped[list | None] = mapped_column(JSON)  # 매칭 BP 없으면 빈 리스트
    rationale: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[Priority | None] = mapped_column(_enum(Priority))
    status: Mapped[str] = mapped_column(String(20), default="proposed")


class BestPractice(Base):
    __tablename__ = "best_practices"

    bp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    indicator_ids: Mapped[list] = mapped_column(JSON)  # 관련 지표
    industry: Mapped[str | None] = mapped_column(String(100))  # None = 전 업종
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(300))


class Outbox(Base):
    __tablename__ = "outbox"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.case_id"), index=True)
    message_type: Mapped[str] = mapped_column(String(30))  # saq_request / reminder / training / survey
    recipient: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[OutboxStatus] = mapped_column(_enum(OutboxStatus), default=OutboxStatus.DRAFT)
    created_by: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Approval(Base):
    __tablename__ = "approvals"

    approval_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    target_type: Mapped[str] = mapped_column(String(30))  # tier / screening / improvement / outbox
    decision: Mapped[ApprovalDecision] = mapped_column(_enum(ApprovalDecision))
    reason: Mapped[str | None] = mapped_column(Text)
    approver: Mapped[str] = mapped_column(String(100))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    case_id: Mapped[str | None] = mapped_column(String(20), index=True)
    actor_type: Mapped[ActorType] = mapped_column(_enum(ActorType))
    actor: Mapped[str] = mapped_column(String(100))  # Agent 이름 또는 사람 ID
    action: Mapped[str] = mapped_column(String(100))
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str | None] = mapped_column(String(40))
    detail: Mapped[dict | None] = mapped_column(JSON)  # 원본 증빙 전문 기록 금지


class LlmUsage(Base):
    """SPEC 10장 비용 관리: 호출별 토큰·추정 비용."""

    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case_id: Mapped[str | None] = mapped_column(String(20), index=True)
    agent: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
