# Progress Management

`PROGRESS.md`는 복잡한 Rhymework 프로젝트의 single source of truth다. Project Orchestration Mode 또는 장기 scoped feature에서만 사용한다. 한 줄 수정, 작은 bug fix, 단순 설명, 작은 문서 수정에는 만들지 않는다.

## 기본 구조

기존 프로젝트 progress 문서가 호환 구조를 이미 갖고 있지 않다면 아래 schema를 사용한다.

```markdown
# Project Progress

Last Updated:
Overall Progress: 0%

## Status

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

## Summary

| Epic | Weight | Progress | Status | Owner |
|---|---:|---:|---|---|

## Tasks

| ID | Epic | Task | Owner | Complexity | Model | Reasoning | Status | Progress | Depends On | Validation |
|---|---|---|---|---|---|---|---|---:|---|---|

## Active Work

## Blockers

## Decisions

## Latest Integration Result
```

프로젝트에 필요하면 extra column을 추가할 수 있다. 단 helper와 다음 session이 읽을 수 있도록 required column은 유지한다.

## Table contract

- `Summary` table은 `Epic`, `Weight`, `Progress`, `Status`, `Owner` column을 가진다.
- `Tasks` table은 `ID`, `Epic`, `Task`, `Owner`, `Complexity`, `Model`, `Reasoning`, `Status`, `Progress`, `Depends On`, `Validation` column을 가진다.
- `Depends On`은 `-` 또는 comma-separated task ID 목록이다.
- `Progress`는 기계적으로 계산한다. `DONE` task는 `100%`, 나머지 status는 모두 `0%`다. 주관적인 부분 진척률을 만들지 않는다.
- Epic progress = DONE task 수 / 해당 epic task 수 × 100. Overall progress = sum(epic weight × epic progress) / sum(weight). Weight는 양의 유한 수다. 단순 평균을 원하면 모든 task를 weight=1인 단일 epic으로 묶는다. 빈 프로젝트는 `0%`다. 소수점 둘째 자리까지 표시한다.
- 반올림으로 미완료 작업이 100%가 되지 않도록 미완료 aggregate는 최대 99.99%로 표시한다.
- Epic 상태 우선순위: 모두 DONE → DONE; 하나라도 BLOCKED → BLOCKED; IN_PROGRESS 있음 → IN_PROGRESS; REVIEW 있음 → REVIEW; DONE+TODO 혼합 → IN_PROGRESS; 그 외 TODO.
- `DONE` task의 `Validation`은 반드시 `PASS: `로 시작하고 evidence를 적는다. 예: `PASS: npm test`, `PASS: helm template`, `PASS: deployed to dev EKS and smoke /health passed`.
- Helper는 shape와 consistency를 검사한다. Leader는 evidence가 실제이고 task에 충분한지 별도로 검토한다.

`python3 <skill>/scripts/progress.py <project>/PROGRESS.md`는 읽기 전용 검사다. 유효하면 READY/epic/overall JSON, 불일치하면 stderr와 nonzero exit를 반환한다. 현재 snapshot만 검사하며 상태 전이 이력이나 실제 테스트 성공을 증명하지 않는다. 표 셀 안의 pipe 대신 `&#124;`를 사용하고 셀은 한 줄로 쓴다. 기존 비호환 progress 문서는 허락 없이 덮어쓰지 말고 수동으로 동일 규칙을 적용하거나 명시적으로 schema를 정리한다.

## 상태 전이

허용 status:

- `TODO`: 아직 시작하지 않음.
- `IN_PROGRESS`: 배정됐거나 구현 중.
- `REVIEW`: 구현이 끝났고 validation 또는 독립 review 대기.
- `DONE`: 구현과 필요한 validation이 모두 성공.
- `BLOCKED`: credential, access, secret, approval, 외부 권한, unresolved upstream dependency가 필요해 진행 불가.

정상 전이:

```text
TODO -> IN_PROGRESS -> REVIEW -> DONE
```

검증 실패는 REVIEW → IN_PROGRESS, blocker 해제는 BLOCKED → TODO로 되돌려 재배정한다. DONE 이후 회귀나 계약 변경이 발견되면 영향받은 Task를 REVIEW/IN_PROGRESS로 다시 열고, 의존한 완료 Task의 증거도 재평가한다. 진척률은 내려갈 수 있으며 이를 감추지 않는다. 일반적인 미완료 dependency 대기는 TODO로 두고, 실제 외부 blocker가 생긴 경우에만 BLOCKED를 쓴다.

`BLOCKED`는 실제 blocker에만 사용한다. 구현이 어렵다, 설계가 복잡하다, 파일이 많다, 시간이 오래 걸린다는 blocker가 아니다. 이 경우 task를 쪼개거나 model을 escalation하거나 다른 READY task를 배정한다.

`DONE`은 "코드를 작성했다"는 뜻이 아니다. Task completion criteria가 evidence와 함께 통과했다는 뜻이다. Integration, deployment, smoke test가 요청 범위라면 각각 별도 task로 관리한다.

## 작성 권한

Leader가 `PROGRESS.md`의 기본 writer다. Subagent는 파일을 동시에 수정하지 않고 status event를 leader에게 보고한다.

Leader는 특정 subagent에게 명시적인 exclusive handoff를 줄 수 있다. 이때 다음을 적는다.

- task ID
- 허용 status change
- 허용 row 또는 section
- 기대 validation evidence
- write ownership이 leader에게 돌아오는 time 또는 event

여러 agent가 `PROGRESS.md`를 동시에 수정하지 않게 한다. Subagent가 새 필수 작업을 발견하면 task proposal을 위로 보고한다. Leader가 ID, dependency, complexity, owner, model, reasoning, validation을 포함해 새 row를 추가한다.

## Dependency graph와 READY 선택

`Depends On`을 task graph로 취급한다. Task는 다음 조건을 만족할 때 READY다.

- status가 `TODO`
- 모든 dependency task가 `DONE`
- file ownership을 conflict 없이 배정 가능
- 필요한 credential 또는 외부 access가 이미 있거나 task에 필요 없음

Helper의 ready_tasks는 앞의 상태/의존성 두 조건까지만 계산한다. 실제 dispatch 직전에 리더가 소유권·외부 접근 조건을 추가로 확인한다.

모든 TODO를 실행하지 않는다. READY task만 실행한다. 복잡한 프로젝트에서는 보통 2~4개를 병렬로 진행한다. Architecture는 implementation보다 먼저, contract는 integration보다 먼저, schema는 repository보다 먼저, core engine은 integration test보다 먼저 둔다.

Task가 `BLOCKED`가 되어도 독립 READY task는 계속 진행한다. `Blockers`에는 missing item, affected tasks, owner, next unblock action을 적는다.

## Progress update event

다음 순간에는 `PROGRESS.md`를 갱신한다.

- project bootstrap 또는 resume
- task assignment: `TODO -> IN_PROGRESS`
- implementation complete: `IN_PROGRESS -> REVIEW`
- validation success: `REVIEW -> DONE`
- 실제 blocker: `BLOCKED`
- 새 필수 task 발견
- integration result, deployment result, smoke result, major decision
- final report 준비

모든 update는 task, decision, validation command, deployment evidence, blocker 중 하나로 추적 가능해야 한다. 새로 발견한 필수 작업을 다른 task 안에 숨기지 말고 새 row로 추가하고 dependency를 연결한다.

## Resume protocol

새 Rhymework session이 프로젝트를 이어받으면 다음 순서로 읽는다.

1. `AGENTS.md`
2. `PROGRESS.md`
3. `docs/MASTER_PLAN.md`
4. 최신 `git status`와 diff
5. 기록된 최신 test, deployment, smoke evidence
6. `BLOCKED`, `IN_PROGRESS`, `REVIEW` task

그 다음 다음 READY task를 선택한다. 기존 plan이 없거나, 낡았거나, 저장소와 모순되는 경우가 아니면 전체 프로젝트를 처음부터 다시 계획하지 않는다.

## Completion과 100%

다음 필수 항목이 모두 DONE이 되기 전에는 전체 프로젝트 complete 또는 `100%`를 보고하지 않는다.

- 필수 implementation
- 필수 test, lint, typecheck, build 또는 동등 validation
- integration validation
- 요청됐거나 필요한 target environment deployment
- 요청됐거나 필요한 smoke test
- documentation sync
- known issues와 blockers 기록

Target environment validation이 access 부족 때문에 불가능하면 관련 task를 `BLOCKED`로 유지하고 전체 progress를 정직하게 보고한다. 사용자가 요구를 바꾸지 않았다면 development deployment 요구를 local-only 증거로 대체하지 않는다.
