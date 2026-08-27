# 공급망 ESG 진단·컨설팅 대시보드 (triplej)

기업의 공급망 ESG 진단/컨설팅 업무를 단계별로 구조화한 정적 웹 대시보드입니다.
진단 8단계 실행 체계, 조직별 R&R(RACI 매트릭스), 국내 대기업(삼성전자·SK하이닉스·현대차·LG전자·POSCO) 벤치마킹, 기준 프레임워크를 담았습니다.

## 구성

| 파일 | 내용 |
|------|------|
| `index.html` | 랜딩 페이지 — 4개 버전 진입 |
| `dashboard.html` | 통합 대시보드 (기본) |
| `sian-a.html` | 시안 A · 감사 원장 (Audit Ledger, 문서형) |
| `sian-b.html` | 시안 B · 관제 콘솔 (Control Room, 다크 대시보드) |
| `sian-c.html` | 시안 C · 컨설팅 브리프 (Brand Consulting) |

## 배포 (Vercel)

빌드 과정이 없는 순수 정적 사이트입니다.

1. [vercel.com](https://vercel.com) 로그인 → **Add New… → Project**
2. GitHub의 `cooljihwan/triplej` 저장소 Import
3. Framework Preset은 **Other**(정적), 별도 빌드 명령 없음 → **Deploy**

배포되면 루트(`/`)에서 `index.html`이 서빙됩니다.

## 출처

각 사 정보는 공개된 지속가능경영보고서·공시 및 언론 보도 기준이며, 최신 연도 보고서로 상세 수치 확인을 권장합니다.
