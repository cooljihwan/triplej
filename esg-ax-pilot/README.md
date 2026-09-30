# SKT 공급망 ESG 진단·컨설팅 내재화 AX (Multi-Agent)

외주(Click ESG)로 맡기던 협력사 자가진단 검증·개선 컨설팅을 SKT가 직접 수행하도록 돕는 시스템. 진단(검증) / 컨설팅 / 운영(보조) Agent가 공유 DB의 케이스 상태를 기준으로 동작한다.
요구사항은 [`SPEC.md`](SPEC.md), 작업 규칙은 [`CLAUDE.md`](CLAUDE.md), 가정은 [`docs/assumptions.md`](docs/assumptions.md).

## 진행 현황 (SPEC 8장)

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 프로젝트 골격, config, DB 모델, 샘플 데이터 | ✅ 완료 |
| 2 | 지표 마스터·버전 + Click ESG 과거 데이터 적재 | ⏳ |
| 3 | 상태 머신 + audit log | ⏳ |
| 4 | 점수 계산 | ⏳ |
| 5 | 증빙 파일 변환 | ⏳ |
| 6 | 진단 Agent: 증빙 스크리닝 · 검증 우선순위 | ⏳ |
| 7 | 담당자 검증 화면 | ⏳ |
| 8 | 진단 Agent: 검토의견 초안 | ⏳ |
| 9 | 컨설팅 Agent | ⏳ |
| 10 | 운영 Agent (보조) | ⏳ |
| 11 | 품질 평가 (외주 판정 비교) | ⏳ |
| 12 | 협력사 웹사이트 (추후) | ⏳ |

## 실행

```bash
cd esg-ax-pilot
pip install -r requirements.txt
cp .env.example .env              # API 키는 .env 에만
python -m scripts.seed_sample     # 샘플 협력사 20곳 → esg_pilot.db
python -m pytest
```
