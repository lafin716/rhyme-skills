# 문서 bootstrap / reuse

Project Orchestration 모드의 새 문서가 필요할 때만 읽는다. 기존 AGENTS·계획·architecture·progress의 위치/내용을 먼저 조사한다. 동등한 문서가 있으면 경로를 MASTER_PLAN과 handoff에 매핑하고 보완한다. 기존 파일과 OMX runtime marker를 템플릿으로 덮어쓰지 않는다. 새 AGENTS는 프로젝트의 실행 규칙이며 상위 지침을 무효화하지 않는다.

## 기본 문서

| 기본 경로 | 생성 자료 | 적용 |
|---|---|---|
| docs/MASTER_PLAN.md | [MASTER_PLAN](../templates/MASTER_PLAN.md) | 구현 전 목표·범위·계약·단계·완료 기준 |
| docs/ARCHITECTURE.md | [ARCHITECTURE](../templates/ARCHITECTURE.md) | component·data flow·결정과 근거 |
| docs/TEST_STRATEGY.md | [TEST_STRATEGY](../templates/TEST_STRATEGY.md) | 실제 명령·환경·통과 조건 |
| PROGRESS.md | [PROGRESS](../templates/PROGRESS.md) | 상태의 유일한 장부 |
| AGENTS.md | [AGENTS](../templates/AGENTS.md) | 없을 때만 생성; 있으면 필요한 규칙을 보존하며 추가 |

작은 작업에서는 위 파일을 생성하지 않는다. 템플릿의 `{{...}}`는 실제 값으로 바꾸고, 적용 불가 항목에는 이유를 적는다. 미확정 값은 결정을 담당할 Task/질문과 연결한다. 없는 정보나 실행 결과를 채워 넣지 않는다.

## 선택 문서

API_SPEC은 공유 API, DOMAIN_MODEL은 복잡한 용어/상태, SECURITY는 인증/운영 경계, TROUBLESHOOTING은 재현된 장애가 있을 때 생성한다. 작은 내용은 기존 architecture/plan의 섹션으로 충분하다. 파일 수를 늘리는 것이 목표가 아니다.

새 서버/클러스터 또는 개발 배포 절차가 필요하면 [DEV_SERVER_SETUP](../templates/DEV_SERVER_SETUP.md)을 docs/DEV_SERVER_SETUP.md 또는 기존 DEPLOYMENT.md에 적용한다. credential은 획득 방법/이름/권한만 기록한다. 실제 배포 후 명령·의존성·verification·rollback의 차이를 반영한다. 실행 전에는 계획, 실행 후에는 실제 결과를 분명히 구별한다.

Task 위임에는 [task-handoff](../templates/task-handoff.md)를 사용한다. 작은 위임은 동일 필드를 메시지로 전달해도 된다. 장기 작업은 프로젝트의 기존 handoff 경로나 docs/handoffs/<task-id>.md에 둔다. 이는 context/증거 문서이며 최신 상태는 항상 PROGRESS를 확인한다.
