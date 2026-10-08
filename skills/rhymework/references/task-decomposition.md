# Task Graph와 분해

각 Task는 ID, 요구사항 연결, Epic, Owner, 파일 소유권, Complexity, Model/Reasoning, Depends On, Expected Output, Validation, Completion criteria를 가진다. 표에 없는 상세 내용은 MASTER_PLAN의 Task contracts 또는 task handoff에 둔다. PROGRESS만 상태를 저장하며 계획/런타임 queue에 별도 상태 장부를 만들지 않는다.

## 분해 기준

Architecture → Contracts → 독립 구현 → Integration → 필요한 배포 → Smoke → Documentation sync 순으로 검증 가능한 경계를 만든다. Task는 검증 가능한 결과 단위이고 agent는 여러 관련 Task를 맡을 수 있다. 1개 Task당 1개 agent 규칙은 없다. 단순 테스트/문서는 관련 구현 묶음에 포함할 수 있으나 최종 문서 동기화는 실제 환경 검증 뒤에 둔다.

- 병렬 가능: 확정된 계약 아래 Backend / Frontend, 독립 component, 안정된 인터페이스의 tests, Infra manifest / UI, 확정 설계 설명 / 구현.
- 순차 필요: Architecture → 구현, API Contract → frontend API 연동, Schema → repository, Core Engine → integration test 실행.
- Backend가 persistence/repository를 구현하고 별도 DB Task가 schema를 결정한다면 Backend의 Depends On에 DB schema Task를 넣는다. “서로 다른 디렉터리”라는 이유만으로 이 의존성을 생략하지 않는다. schema 계약이 이미 구체적으로 확정된 경우에만 migration 구현과 독립 API shell 등을 병렬화한다.
- Frontend가 API mock으로 먼저 작업하면 mock 계약 검증과 실제 API 연동을 다른 Task로 나누고 실제 연동은 Backend 완료에 의존한다.
- Infra manifest와 앱 구현은 병렬 가능하지만 실제 deployment는 앱 build·infra 검증·필요한 권한에 의존한다.
- graph는 순환이 없어야 한다. 누락된 dependency, 자기 의존, 중복 ID를 수정한 뒤 배정한다.
- 독립성은 파일뿐 아니라 공유 resource·migration·환경 변경도 고려한다. 개발 cluster의 동시 migration/배포는 리더가 직렬화한다.

## 대표 예: EKS 공용 k6 플랫폼 MVP

요청: 계획과 PROGRESS를 관리하며 Frontend / Backend / Infra / k6를 병렬 구현하고 개발 EKS에서 Smoke Test한다.

```text
Repository Inspection → Project Orchestration
 → MASTER_PLAN + ARCHITECTURE + TEST_STRATEGY + PROGRESS + AGENTS(reuse)
 → Architecture / Contract 검토
 → Task Graph / Ownership
     ├ Backend: STANDARD / medium (Terra 후보)
     ├ Frontend: STANDARD / medium (Terra 후보)
     ├ k6 Engine: ADVANCED / high (Sol 후보)
     └ Infra: ADVANCED / high (Sol 후보)
 → Integration + tests/build
 → Independent final review: PREMIUM / high (Astra 후보)
 → Development EKS Deploy → integration / Smoke Test
 → Documentation Sync → PROGRESS 100% → Final Report
```

모델 표기는 목표 tier이며 실제 모델은 현재 도구/역할로 해석한다. 대표 계약에는 시나리오 입력, 실행 생성/조회/취소, 인증·권한, 실행 상태 전이, 결과 저장, 배포 image/config 형식이 포함될 수 있다. 사용자의 MVP 범위에 맞게 선택한다. 부하 규모·대상 allowlist·cleanup·개발 namespace를 확정한 뒤 승인된 대상만 실행한다.

예시 ID와 소유권: ARCH-001(main, docs), CONTRACT-001(main, contracts), BE-001(backend, apps/api), FE-001(frontend, apps/web), K6-001(engine, engine), INF-001(infra, deploy). 마지막 네 Task는 CONTRACT-001에 의존한다. INT-001은 네 구현에, REVIEW-001은 INT-001에, DEPLOY-001은 REVIEW-001에, SMOKE-001은 DEPLOY-001에, DOC-001은 SMOKE-001에 의존한다. 독립 docs 초안은 먼저 작성해도 최종 sync를 대체하지 않는다.

EKS credential이 없으면 DEPLOY-001을 BLOCKED로 유지한다. 의존 없는 로컬 테스트·문서 초안은 계속하고 Smoke를 성공했다고 보고하거나 100%로 바꾸지 않는다.
