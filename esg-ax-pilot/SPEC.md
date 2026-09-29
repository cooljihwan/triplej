# 공급망 ESG AX 파일럿 — 개발 요구사항 (SPEC)

> 이 문서는 Claude Code가 읽고 개발하기 위한 요구사항 문서다.
> `[TBD]` 표시는 업무 담당자가 채워야 하는 항목이며, 채워지기 전에는 샘플 값으로 개발하고 교체 가능하게 만든다.

---

## 0. Claude Code 작업 원칙 (반드시 준수)

1. 한 번에 전체를 만들지 않는다. **8장 개발 단계 순서대로, 지시받은 단계만** 구현한다.
2. 각 단계가 끝나면 테스트를 실행하고, 무엇을 만들었는지와 다음 단계에서 확인이 필요한 사항을 요약한다.
3. 요구사항이 불명확하면 추측해서 크게 만들지 말고 질문하거나, 가장 단순한 형태로 만들고 가정을 `docs/assumptions.md`에 기록한다.
4. **LLM은 판정과 근거 작성만 한다. 점수 계산, 상태 변경, 메일 발송은 반드시 일반 코드가 한다.**
5. 파일럿 기간에는 **실제 메일 발송 금지**. 모든 메일은 `outbox` 테이블에 저장만 하고 화면에서 미리보기만 한다(dry-run).
6. API 키 등 비밀값은 `.env`로만 관리하고 코드·로그에 남기지 않는다.

---

## 1. 프로젝트 개요

- **목적**: 공급망 ESG 진단·컨설팅·운영 업무 중 반복 업무를 AI Agent로 자동화하여 업무 효율을 높이고 진단 대상을 확대한다.
- **이번 범위**: 11월 CEO 세미나 보고용 **파일럿(Step1 필수 기능)**.
- **데이터 원천**: 기존 플랫폼 Click ESG의 **엑셀 내보내기 파일** (API 연동은 이번 범위 아님).
- **사용 데이터**: 과거 진단 데이터(익명화본)로 시연.

### 1.1 이번 범위 (Pilot)
| Agent | 포함 기능 |
|---|---|
| 진단 Agent | ESG Risk Tier 분류, 증빙 데이터 정합성 1차 스크리닝 |
| 컨설팅 Agent | 진단 결과 기반 개선 필요사항 도출 및 Best Practice 매칭 |
| 운영 Agent | 자가진단 발송·리마인드 메일 초안, 응답·진행 현황 점검, 만족도 조사 취합 |

### 1.2 이번 범위 아님 (Step2 이후)
진단 결과 보고서 초안, 벤치마크 Gap 분석, 컨설팅 대상 선정, 실사 체크리스트·인터뷰 요약, 협력사 문의 답변 초안, 신용평가·뉴스 제공, Click ESG API 연동, 실제 메일 발송, 사내 SSO.
→ 단, **나중에 모듈만 추가하면 되도록** 구조를 설계한다.

---

## 2. 기술 스택

- Python 3.11+
- LLM: Anthropic Claude API
  - 기본 모델: `claude-sonnet-5-5` (판정·매칭)
  - 단순 분류·요약: `claude-haiku-4-5-20251001`
  - 모델명은 `config.py`에서 한 곳으로 관리
- Agent 구현: Claude Agent SDK(Python) 또는 Anthropic Python SDK의 tool use. 구현 전 최신 공식 문서를 확인할 것.
- DB: SQLite (파일럿) — SQLAlchemy 사용, 추후 PostgreSQL 전환 가능하게
- 화면: Streamlit (담당자 검토·승인 화면)
- 파일 처리: pandas/openpyxl(엑셀), pdfplumber 또는 PyMuPDF(PDF 증빙)
- 테스트: pytest

### 2.1 폴더 구조 (권장)
```
esg-ax-pilot/
├─ SPEC.md
├─ CLAUDE.md
├─ .env.example
├─ config.py
├─ data/
│  ├─ input/          # Click ESG 엑셀, 증빙 PDF
│  ├─ reference/      # 평가 기준표, Risk Tier 기준, Best Practice 라이브러리
│  └─ samples/        # 테스트용 샘플
├─ app/
│  ├─ db/             # 모델, 마이그레이션
│  ├─ ingest/         # 엑셀·PDF 적재
│  ├─ agents/
│  │  ├─ diagnosis/   # 진단 Agent + 내부 모듈
│  │  ├─ consulting/  # 컨설팅 Agent + 내부 모듈
│  │  └─ operations/  # 운영 Agent + 내부 모듈
│  ├─ scoring/        # 점수 계산 (규칙 기반 코드, LLM 사용 금지)
│  ├─ workflow/       # 상태 머신(오케스트레이터)
│  ├─ mail/           # outbox, 메일 템플릿
│  └─ ui/             # Streamlit 화면
├─ prompts/           # Agent별 시스템 프롬프트 (코드와 분리)
├─ tests/
└─ docs/
```

---

## 3. 전체 구조

- **Agent 3개**(진단/컨설팅/운영)는 서로 직접 호출하지 않는다.
- 모든 Agent는 **공유 DB의 협력사 케이스(case)**를 읽고, 결과를 정해진 테이블에 기록한다.
- **오케스트레이터는 LLM이 아니라 상태 머신 코드**다. 케이스의 `status`가 바뀌면 다음 작업을 실행한다.
- 사람(사내 전문가)의 확인이 필요한 지점은 **승인 대기 상태**로 멈추고, 승인 화면에서 승인·반려한다.
- 협력사에게 나가는 모든 연락(메일)은 **운영 Agent만** 생성한다.

```
[Click ESG 엑셀] → 적재 → 진단 Agent → (전문가 승인) → 컨설팅 Agent → (전문가 승인) → 운영 Agent
                                 ↑                                              │
                                 └──────────── 공유 DB (case 상태값) ←──────────┘
```

---

## 4. 상태 머신 (case.status)

| 상태 | 의미 | 다음 작업 주체 |
|---|---|---|
| `IMPORTED` | 협력사 데이터 적재 완료 | 진단: Risk Tier 분류 |
| `TIER_PENDING_APPROVAL` | Tier 분류 결과 승인 대기 | 사내 전문가 |
| `SAQ_REQUESTED` | 자가진단 요청 메일 초안 생성됨 | 운영: 응답 현황 추적 |
| `SAQ_RECEIVED` | 자가진단 응답·증빙 적재 완료 | 진단: 정합성 스크리닝 |
| `SCREENING_PENDING_APPROVAL` | 스크리닝 결과 검토 대기 | 사내 전문가 |
| `DIAGNOSIS_CONFIRMED` | 진단 결과 확정 | 컨설팅: 개선과제·BP 매칭 |
| `IMPROVEMENT_PENDING_APPROVAL` | 개선과제 우선순위 확정 대기 | 사내 전문가 |
| `MONITORING` | 개선 이행 점검 중 | 운영 |
| `SURVEY` | 만족도 조사 진행 | 운영 |
| `CLOSED` | 종료 | - |

- 반려 시 이전 상태로 되돌리고 반려 사유를 기록한다.
- 모든 상태 변경은 `audit_log`에 남긴다(누가, 언제, 무엇을, 이전/이후 상태).

---

## 5. 데이터 모델 (초안)

| 테이블 | 주요 컬럼 |
|---|---|
| `suppliers` | supplier_id, 회사명(익명화 가능), 업종, 국가, 거래규모, 거래유형 `[TBD: Click ESG 컬럼 매핑]` |
| `cases` | case_id, supplier_id, 진단연도, status, risk_tier, created_at, updated_at |
| `saq_responses` | case_id, 문항ID, 영역(E/S/G), 응답값, 증빙 필요 여부 |
| `evidence_files` | case_id, 문항ID, 파일경로, 파일유형, 발급일, 유효기간 |
| `findings` | case_id, 문항ID, 판정(적합/불일치/증빙누락/확인필요), 근거(문서명·페이지·원문 요약), 확신도, 생성 Agent |
| `scores` | case_id, 지표ID, 점수, 계산근거 (코드 계산) |
| `improvement_items` | case_id, 지표ID, 개선 필요사항, 매칭된 BP ID, 우선순위, 상태 |
| `best_practices` | bp_id, 관련 지표, 업종, 내용, 출처 |
| `outbox` | message_id, case_id, 유형, 수신자, 제목, 본문, 상태(draft/approved), 생성 Agent |
| `approvals` | approval_id, case_id, 대상유형, 결정(승인/반려), 사유, 승인자, 일시 |
| `surveys` | case_id, 문항, 응답 |
| `audit_log` | 시각, 주체(Agent/사람), 동작, 상세 |

---

## 6. Agent별 상세

### 공통 규칙
- 모든 Agent 출력은 **JSON 스키마로 검증**한다(pydantic). 검증 실패 시 1회 재시도, 그래도 실패하면 `확인필요`로 기록.
- 모든 판정에는 **근거(문서명, 페이지 또는 문항, 원문 요약)**가 있어야 한다. 근거 없는 판정은 저장하지 않는다.
- 시스템 프롬프트는 `prompts/` 폴더의 파일로 관리한다.
- 평가 기준표처럼 반복 투입되는 긴 문서는 프롬프트 캐싱을 적용한다.

### 6.1 진단 Agent (`app/agents/diagnosis/`)

**모듈 A — Risk Tier 분류**
- 입력: `suppliers` 정보, `data/reference/risk_tier_criteria` `[TBD: 분류 기준표]`
- 처리: 기준표의 정량 규칙(업종·국가·거래규모 등)은 코드로 1차 계산, 규칙으로 판단이 어려운 경우만 LLM이 보조 판단
- 출력:
```json
{"supplier_id": "S001", "risk_tier": "High|Medium|Low", "reasons": ["..."], "rule_based": true, "confidence": 0.0}
```
- 완료 후 상태: `TIER_PENDING_APPROVAL`

**모듈 B — 증빙 정합성 1차 스크리닝**
- 입력: `saq_responses`, `evidence_files`
- 점검 항목:
  1. 증빙 필요 문항에 증빙이 첨부됐는가
  2. 증빙 내용이 응답과 일치하는가 (예: "ISO 14001 보유" 응답 ↔ 인증서의 회사명·범위)
  3. 인증서·문서의 유효기간이 진단 기준일 기준 유효한가
  4. 응답 간 모순이 있는가 (예: "정책 없음"인데 "정책 교육 실시")
- 출력 (`findings`에 문항별로 저장):
```json
{"case_id": "C001", "question_id": "E-03", "verdict": "적합|불일치|증빙누락|확인필요",
 "evidence": {"file": "iso14001.pdf", "page": 1, "summary": "인증 범위: 본사 제조공장"},
 "comment": "응답은 전 사업장이나 인증 범위는 본사 공장에 한정", "confidence": 0.8}
```
- 완료 후 상태: `SCREENING_PENDING_APPROVAL`

**점수 계산 (`app/scoring/`)** — LLM 사용 금지
- 확정된 판정 + 평가 기준표 `[TBD: 지표별 배점표]`로 지표별 점수를 계산해 `scores`에 저장.

### 6.2 컨설팅 Agent (`app/agents/consulting/`)

**모듈 — 개선 필요사항 도출 및 Best Practice 매칭**
- 입력: `scores`, `findings`, `best_practices` `[TBD: BP 라이브러리 초기 데이터]`
- 처리:
  1. 기준 점수 미달 지표와 `불일치/증빙누락` 판정 항목에서 개선 필요사항 도출
  2. 업종·지표가 맞는 BP를 검색하여 매칭 (없으면 "매칭 BP 없음"으로 표시, 지어내지 말 것)
  3. 우선순위 제안(시급성·영향도), 최종 확정은 사람
- 출력:
```json
{"case_id": "C001", "items": [
  {"indicator_id": "S-05", "issue": "...", "priority": "상|중|하", "bp_ids": ["BP-012"], "rationale": "..."}
]}
```
- 완료 후 상태: `IMPROVEMENT_PENDING_APPROVAL`

### 6.3 운영 Agent (`app/agents/operations/`)

**모듈 A — 메일 초안 생성** (자가진단 요청, 리마인드, 교육 안내, 만족도 조사 요청)
- 템플릿: `app/mail/templates/` `[TBD: 실제 메일 문안]`
- LLM은 템플릿의 빈칸과 협력사별 안내 문구만 채운다.
- `outbox`에 `draft`로 저장, 승인 후 `approved`. **파일럿에서는 실제 발송 없음.**

**모듈 B — 진행 현황 점검**
- 매일 1회(또는 버튼 실행) 전체 케이스 상태를 점검하여:
  - 기한 초과 미응답 협력사 → 리마인드 초안 생성
  - 승인 대기로 N일 이상 멈춘 건 → 담당자 알림 목록
- 결과는 대시보드에 표시. 이 모듈은 대부분 **일반 코드**로 구현, LLM은 요약 문장 작성에만 사용.

**모듈 C — 만족도 조사 취합**
- 응답 취합 및 주관식 응답 요약(긍정/개선요청 분류).

---

## 7. 담당자 화면 (Streamlit)

1. **대시보드**: 상태별 케이스 수, Tier 분포, 기한 초과 건, 승인 대기 건
2. **승인함**: 승인 대기 항목 목록 → 상세(Agent 판정 + 근거 + 원본 파일 링크) → 승인/반려(사유 입력)
3. **케이스 상세**: 협력사별 전체 이력(판정, 점수, 개선과제, 메일, audit log)
4. **메일 미리보기**: outbox 초안 확인·수정·승인
5. **데이터 업로드**: Click ESG 엑셀, 증빙 파일 업로드

---

## 8. 개발 단계 (Claude Code에 한 단계씩 지시)

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| 1 | 프로젝트 골격, config, DB 모델, 샘플 데이터 생성 | 샘플 협력사 20곳이 DB에 적재됨 |
| 2 | Click ESG 엑셀 적재기 (컬럼 매핑은 설정 파일로 분리) | 실제 내보내기 파일 적재 성공 |
| 3 | 상태 머신 + audit log | 상태 전이 테스트 통과 |
| 4 | 진단 모듈 A (Risk Tier) | 샘플 20곳 분류 + 근거 출력 |
| 5 | 진단 모듈 B (증빙 스크리닝) + 점수 계산 | 샘플 증빙으로 판정·근거 생성 |
| 6 | Streamlit 승인함·대시보드 | 승인/반려로 상태가 바뀜 |
| 7 | 컨설팅 Agent (개선과제·BP 매칭) | 확정 케이스에 개선과제 생성 |
| 8 | 운영 Agent (메일 초안, 현황 점검, 만족도 취합) | outbox 초안 생성·승인 |
| 9 | 정확도 평가 + 시연 시나리오 | 11장 평가 리포트 생성 |

---

## 9. 보안·데이터 원칙

- 파일럿 데이터는 **익명화본** 사용 (회사명·담당자명·연락처 마스킹).
- 외부 API 전송 대상 데이터 범위는 사내 보안 검토 결과에 따른다 `[TBD: 보안 검토 결과]`.
- 로그에 원본 증빙 내용 전문을 남기지 않는다.
- 사용 모델·호출 환경(직접 API / 사내 클라우드 경유)은 `config.py`에서 교체 가능하게 한다.

---

## 10. 비용 관리

- 호출마다 입력·출력 토큰 수와 추정 비용을 DB에 기록하고 대시보드에 표시.
- 급하지 않은 대량 스크리닝은 Batch 처리 옵션을 둔다.

---

## 11. 평가 (CEO 세미나 보고용 근거)

- 과거 진단에서 사람이 내린 판정을 **정답셋**으로 사용 `[TBD: 정답셋 준비]`.
- 측정 지표:
  - 증빙 스크리닝 판정 일치율 (Agent vs 사람)
  - 사람이 놓쳤으나 Agent가 발견한 이슈 건수
  - 협력사 1곳당 처리 시간 (기존 대비)
  - 협력사 1곳당 API 비용
- 결과를 `docs/pilot_report.md`로 자동 생성.

---

## 12. 업무 담당자가 채워야 할 항목 `[TBD]` 목록

1. Click ESG 엑셀 내보내기 샘플 파일과 컬럼 설명
2. ESG Risk Tier 분류 기준표
3. 자가진단 문항 목록과 문항별 증빙 필요 여부
4. 지표별 배점표 및 기준 점수(미달 기준)
5. Best Practice 라이브러리 초기 데이터 (최소 20~30건)
6. 메일 문안 (자가진단 요청, 리마인드, 교육 안내, 만족도 조사)
7. 정답셋 (과거 사람 판정 결과, 최소 협력사 20곳)
8. 보안 검토 결과 (외부 API 사용 가능 범위, 사용 환경)
