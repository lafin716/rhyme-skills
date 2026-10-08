# Project Orchestration

## 시작 / 재개

새 작업은 저장소와 요구사항을 조사하고 기존 계획을 재사용한다. 재개 시 **AGENTS.md → PROGRESS.md → MASTER_PLAN.md → git status/diff → 최근 테스트 증거 → BLOCKED/IN_PROGRESS** 순으로 읽는다. 경로가 다르면 계획에 기록된 실제 경로를 따른다. Git이 없으면 파일 상태와 이전 handoff로 대체한다.

작업 방식이 생략된 결과 중심 요청도 동일하게 처리한다. 사용자에게 문서 이름, agent 역할, 모델 tier, 검증 단계를 지정하게 하지 않는다. 필요한 작업 경계와 완료 기준을 먼저 추론하고 프로젝트 모드이면 이 절차 전체를 적용한다. Frontend/Backend/Infra/k6는 예시이며 고정 필수 목록이 아니다. 기존 기능과 요청의 의미로 필요한 영역만 선택한다.

진행 중 Task의 agent가 실제 살아 있는지 먼저 확인한다. 실행 중인 agent와 중복 배정하지 않는다. 중단된 작업은 diff·로그·검증 결과를 인수한 뒤 REVIEW 또는 재시작할 TODO로 조정한다. 검증이 오래됐거나 코드가 바뀌었다면 필요한 검사만 다시 수행한다.

## 부트스트랩과 계획

[project-templates.md](project-templates.md)를 따라 필요한 문서만 생성/보완한다. Goal·Requirements·Non-goals·Definition of Done과 실제 target environment를 먼저 확정한다. 합리적 구현 선택은 리더가 결정하고, 제품 범위/권한/파괴적 변경에 실질적으로 영향 주는 미확정 사항만 질문한다.

Architecture와 공유 계약을 리더가 작성한다. 다수 요구사항이나 아키텍처 결정은 설치된 architect/critic의 독립 검토를 받아 구체적 지적을 반영한다. 해당 표면이 없으면 직접 검토했다는 한계를 기록한다. 계획만 요청된 경우 여기서 종료한다.

첫 구현 dispatch 전에 문서 경로 점검을 수행한다: MASTER_PLAN, ARCHITECTURE, TEST_STRATEGY, PROGRESS, 적용되는 AGENTS가 실제 존재하는가? 새 서버/cluster가 필요하면 DEV_SERVER_SETUP 또는 기존 배포 가이드의 계획 초안도 존재해야 한다. 배포 후에는 이 초안을 실제 결과로 갱신한다.

계약 Task의 DONE은 “계약을 정의할 예정”이라는 목록으로 충족되지 않는다. 관련 route/schema/state/error/소유 경계의 실제 값과 검토 증거가 있어 하위 작업자가 구현할 수 있어야 한다. 핵심 제품 목적/도메인이 비어 있어 안전하게 결정할 수 없다면 해당 계약은 REVIEW 또는 TODO로 유지하고 필요한 정보를 질문한다. 초안 handoff를 만들 수는 있지만 미완성 계약에 의존한 구현을 READY로 표시하거나 dispatch하지 않는다.

## 반복 실행

1. PROGRESS와 현재 결과를 읽고 dependency/소유권을 검증한다. 선택적으로 `python3 <skill>/scripts/progress.py <project>/PROGRESS.md`로 오류·READY·진척률을 확인한다.
2. TODO 중 모든 선행 Task가 DONE인 작업만 READY로 선택한다. READY는 계산 결과이며 저장 상태가 아니다. BLOCKED를 자동 재시작하지 않는다.
3. [task-decomposition.md](task-decomposition.md)에 따라 독립 작업을 묶고 난이도·모델·effort·선택 이유·파일 소유권을 기록한다. 기본 2–4개이며 실제 슬롯/정책 한도가 더 작으면 그 한도를 따른다.
4. [task-handoff.md](../templates/task-handoff.md)의 최소 context로 네이티브 agent를 호출한다. 리더가 IN_PROGRESS를 반영하고 호출 ID를 Active Work에 기록한다. 성공 확인 없이 실행 중이라고 보고하지 않는다.
5. 결과를 수집하며 한 agent의 BLOCKED가 다른 READY 작업을 막지 않게 한다. 같은 영역의 후속 Task는 기존 agent를 재사용할 수 있다. 하위 agent는 재귀 위임하지 않는다.
6. 구현 완료를 REVIEW로 반영한다. diff, 계약, validation 증거와 위험 작업 독립 리뷰를 확인한다. 통합 변경 후 영향받은 검증을 수행한다. 실제 결과가 계획과 다르면 계획/architecture/계약을 함께 갱신한다.
7. 검증된 개별 Task를 DONE으로 반영한다. 구성요소의 DONE만으로 전체 완료를 선언하지 않고 별도 integration/deploy/smoke/docs Task를 계속한다.
8. PROGRESS의 blocker·decision·integration result·진척률·시각을 갱신하고 다음 READY를 실행한다. READY가 없으면 활동 중 agent를 확인한다. 모두 외부 요인에 막혔다면 필요한 입력/권한과 재개 방법을 보고하며 대기/종료하고 바쁜 재시도는 하지 않는다.

## 소유권과 작업 공간

- apps/api/**, apps/web/**, deploy/** 등의 소유 범위를 실제 저장소에 맞춰 나눈다. 동적 역할 이름은 backend-agent 등으로 붙이되 호출 agent_type은 설치된 역할이다.
- PROGRESS, MASTER_PLAN, 공유 schema/contracts, lockfile, 공통 theme/component는 기본 리더 소유다. 같은 파일 내 서로 다른 줄도 동시 쓰기 소유권으로 나누지 않는다.
- 하위 agent가 공통 변경이 필요하면 리더에게 계약 변경을 요청한다. 리더는 영향받는 작업을 일시 중지하고 계약·의존성·소유권을 조정한 뒤 재개한다.
- 기본 공유 workspace에서는 타인의 변경을 되돌리지 않는다. 서로 다른 agent가 같은 checkout에서 git switch를 실행하지 않는다.
- Git/worktree가 안전하고 기존 정책이 허용할 때만 작업별 branch/worktree를 쓴다. 기존 dirty 변경을 보존하고 리더가 diff/commit을 통합한다. 충돌은 리더가 해결한 뒤 재검증한다. worktree가 불가하면 파일 소유권으로 충분하다.
- 커밋은 기존 Rhymework 정책과 사용자 설정/요청을 우선한다. 승인된 경우 의미 있는 단위만 커밋하고 관련 없는 변경을 포함하지 않는다. push·외부 배포 권한은 커밋 허용에서 추론하지 않는다.

## Context와 보고

전체 대화 대신 계획·architecture·progress·관련 source·실패 증거 경로를 전달한다. 경로 접근이 불가하면 필요한 발췌만 제공한다. 주요 milestone마다 완료된 계약/통합, 현재 실행 영역, blocker를 알린다. 로그에 credential/secret 원문을 저장하지 않는다.
