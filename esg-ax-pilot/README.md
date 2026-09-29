# 공급망 ESG AX 파일럿 (Multi-Agent)

진단 / 컨설팅 / 운영 Agent 3개가 공유 DB의 케이스 상태(`cases.status`)를 기준으로 동작하는 파일럿.
요구사항은 [`SPEC.md`](SPEC.md), 작업 규칙은 [`CLAUDE.md`](CLAUDE.md), 가정은 [`docs/assumptions.md`](docs/assumptions.md).

## 진행 현황 (SPEC 8장)

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 프로젝트 골격, config, DB 모델, 샘플 데이터 | ✅ 완료 |
| 2 | Click ESG 엑셀 적재기 | ⏳ |
| 3 | 상태 머신 + audit log | ⏳ |
| 4 | 진단 모듈 A (Risk Tier) | ⏳ |
| 5 | 진단 모듈 B (증빙 스크리닝) + 점수 계산 | ⏳ |
| 6 | Streamlit 승인함·대시보드 | ⏳ |
| 7 | 컨설팅 Agent | ⏳ |
| 8 | 운영 Agent | ⏳ |
| 9 | 정확도 평가 + 시연 시나리오 | ⏳ |

## 실행

```bash
cd esg-ax-pilot
pip install -r requirements.txt
cp .env.example .env              # API 키는 .env 에만
python -m scripts.seed_sample     # 샘플 협력사 20곳 → esg_pilot.db
python -m pytest
```
