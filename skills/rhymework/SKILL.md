---
name: rhymework
description: Autonomously scope and deliver software build requests, including /rhymework in Claude Code. Infer planning, PROGRESS.md, task dependencies, model routing, parallel agents and target validation from the requested outcome and repository, even when the user only says build it. Preserves UI verification and lightweight small edits.
---

# Rhymework

사용자의 목표를 **계획 → 독립 영역 구현 → 리더 통합 → 독립 리뷰 → 실제 환경 검증**으로 완성한다. 복잡한 작업의 리더는 Lead Architect + Project Manager + Agent Orchestrator다. 기존 UI·이미지 워크플로도 유지한다.

## Claude Code 실행 환경

이 설치본은 Claude Code의 개인 스킬이다. 아래 항목은 본문과 참고 문서의 Codex/OMX 전용 실행 지침을 Claude Code에 대응시키며, 사용자의 범위·승인·프로젝트 지침을 바꾸지 않는다.

- `/rhymework <작업>`으로 호출한다. 전달된 작업 인자를 사용하며, 인자가 없으면 아래 호출 규칙을 따른다.
- 먼저 적용되는 `CLAUDE.md`와 프로젝트가 지정한 `AGENTS.md`를 확인한다. 개인 스킬의 참고 경로는 이 `SKILL.md`가 있는 디렉터리를 기준으로 해석한다.
- Codex 네이티브 서브에이전트 지시는 현재 Claude Code가 노출하는 `Agent` 도구(구버전에서는 `Task`)에 대응한다. 설치된 역할을 확인하고, 같은 역할이 없으면 사용 가능한 범용 에이전트에 executor/reviewer 등의 책임을 명시한다. 같은 파일의 동시 작성자는 하나이며, 구현자와 리뷰어를 분리한다. 서브에이전트가 없으면 순차 수행하고 그 한계를 기록한다.
- `executor`, `architect`, `critic` 등은 작업 책임이다. Codex 전용 `agent_type`, `fork_turns`, `functions.exec`, `collaboration.*`를 Claude에 실제 존재하는 도구/인자로 가정하지 않는다. 읽기·쓰기·검색·셸·진척 도구도 현재 제공되는 도구를 사용한다.
- 모델은 기본적으로 현재 Claude 모델을 상속한다. 작업 난이도와 모델 선택을 기록하되, 별도 선택이 필요하고 실제 지원될 때만 Claude 모델을 사용한다. 참고 문서의 Luna/Terra/Sol/Astra와 GPT 모델명은 논리적 tier 예시이지 Claude의 실행 모델명이 아니다. 지원하지 않는 reasoning effort 인자를 전달하거나 전역 모델 설정을 바꾸지 않는다.
- OMX/team/tmux 런타임은 실제 설치·사용 가능할 때만 사용한다. 필수가 아니며 없으면 네이티브 서브에이전트나 직접 실행으로 같은 소유권·검증 절차를 수행한다. 계획 위치는 기존 저장소 관례를 우선하고, OMX를 사용하지 않는 저장소에서는 `docs/plans/`를 사용한다.
- `agents/openai.yaml`은 원본 Codex 메타데이터로 Claude 실행에는 사용하지 않는다. 스킬 설치 자체가 외부 메시지 전송·운영 배포·파괴적 변경의 추가 승인을 의미하지 않는다.

## 호출과 경계

- Claude Code에서 `/rhymework <작업>`으로 호출한 요청을 해석한다. `$rhymework` 표기는 다른 환경에서 전달된 작업 요청으로만 해석한다.
- 인자가 없으면 현재 미완료 목표를 사용하고, 목표도 없으면 한 번만 간결히 묻는다.
- 계획만 요청하면 계획에서 끝낸다. 채팅만 요청하면 파일을 만들지 않는다. 구현까지 요청했다면 계획 후 승인된 범위에서 계속 실행한다.
- 적용되는 AGENTS.md, 사용자 범위, 기존 변경·저장 데이터·공개 인터페이스를 보존한다. 기존 커밋·배포 정책을 따르며 요청 범위를 확대하지 않는다.
- 이미 위임받은 하위 에이전트는 자기 Task만 수행한다. 재계획·재위임·최종 승인은 리더에게 보고한다.

## 1. 상태 확인과 실행 규모 선택

먼저 저장소, 기존 계획·진행 문서, 구현, 테스트, 디자인, 사용 가능한 도구·역할을 확인한다. 목표와 관찰 가능한 완료 기준을 짧게 알린다. 실제 UI 변경이면 현재 화면도 확인한다.

| 모드 | 선택 기준 | 실행 방식 |
|---|---|---|
| Lightweight | 짧은 설명, 한 파일 bug fix, README 한 줄 등 | 직접 수행·관련 검증. 새 PROGRESS/프로젝트 문서/서브에이전트 불필요 |
| Scoped feature | 한 컴포넌트의 API·페이지·테스트 등 | 간결한 계획과 필요한 구현·검증. 병렬 이익이 있을 때만 위임 |
| Project Orchestration | 아래 복잡성 신호가 여러 개이거나 명시적 프로젝트 관리 요청 | 문서·계약·Task Graph 기반 반복 실행 |

복잡성 신호: 여러 디렉터리/컴포넌트, frontend+backend, infra/Kubernetes/AWS, DB schema, 외부 integration, 장기·다단계 작업, 3개 이상 독립 Task, 병렬 개발, 서버 배포, architecture 결정, 테스트·문서·배포 전체 요청. 단일 키워드나 파일 수만으로 승격하지 않는다. 단순히 “계획”이라는 표현을 썼다고 전체 모드를 강제하지 않는다. PROGRESS와 서브에이전트 병렬 관리를 명시하면 프로젝트 모드를 사용한다.

**사용자는 원하는 결과만 말하면 된다.** 계획·PROGRESS·서브에이전트·모델·reasoning·테스트를 요청문에 나열할 필요가 없다. 요청의 의미와 저장소에서 필요한 구성요소·의존성·운영 환경을 추론하여 위 기준을 적용한다. 복잡한 프로젝트로 판단되면 계획 문서, PROGRESS, 계약, Task Graph, 난이도별 모델/effort, 유용한 병렬 구현, 통합·검증·문서 동기화를 기본 수행하며 각 절차의 사용 여부를 다시 묻지 않는다. “명시되지 않았다”는 이유로 생략하지 않는다.

예: “EKS에서 회사 공용 k6 부하테스트 플랫폼 MVP를 만들어줘”만으로도 실행 관리·UI/API·k6 실행·인프라 등 필요한 경계를 조사하고 프로젝트 모드를 선택한다. 실제 범위는 기존 구현과 MVP 목표에 맞춰 정하며 이미 있는 컴포넌트를 불필요하게 다시 만들지 않는다. 반대로 “버튼 하나 만들어줘”는 작은 작업으로 유지한다. 합리적인 가정과 선택한 모드를 짧게 알리고 진행한다. 핵심 제품 목적이 전혀 없는 요청만 필요한 정보를 묻고, 계획만/코드만/배포 금지 등 사용자의 명시적 제한을 우선한다.

Scoped feature의 계획 위치는 기존 관례 → 쓰기 가능한 `.omx/plans/<task>-plan.md` → `docs/plans/<task>-plan.md` 순이다. 경로 제한 시 허용된 위치나 채팅을 사용한다. 목표·범위·유지할 동작·소유권·공통 계약·선행 의존성·검증을 포함한다. 아키텍처/다수 요구사항 계획은 별도 architect/critic 검토 후 구현한다.

## 2. 프로젝트 실행

프로젝트 모드에서만 [orchestration.md](references/orchestration.md), [task-decomposition.md](references/task-decomposition.md), [progress-management.md](references/progress-management.md)를 읽는다. 기존 프로젝트는 재개 절차로 시작하고 처음부터 다시 계획하지 않는다. 문서가 없거나 보완할 때만 [project-templates.md](references/project-templates.md)를 읽는다.

**READ STATE → CHECK DEPENDENCIES → SELECT READY TASKS → CLASSIFY COMPLEXITY → SELECT MODEL / REASONING → ASSIGN FILE OWNERSHIP → SPAWN SUBAGENTS → COLLECT RESULTS → VALIDATE → INTEGRATE → UPDATE PROGRESS → REPEAT**

SPAWN은 현재 도구가 허용하고 병렬 실행 이익이 있을 때 적용한다. 그렇지 않으면 동일한 소유권 묶음을 순차 수행하고 실제 실행 방식과 제한을 기록한다.

- 구현 전에 MASTER_PLAN·ARCHITECTURE·계약과 Task Graph를 정한다. PROGRESS.md가 Task 상태의 Single Source of Truth다.
- 리더는 아키텍처·계획·계약·의존성·배정·리뷰·통합·충돌 해결·진척·최종 검증을 소유한다. 독립 구현은 소유 범위를 묶어 보통 2–4개 agent에 배정한다. Task 하나마다 새 agent를 만들지 않는다.
- 완료된 dependency를 가진 READY Task만 실행한다. 같은 파일의 동시 작성자는 하나다. 기본적으로 리더만 PROGRESS·계획·공유 계약을 쓴다. 하위 에이전트의 상태 이벤트도 리더가 반영한다.
- `TODO → IN_PROGRESS → REVIEW → DONE`; 진행 불가 시 BLOCKED. 구현만 끝났으면 REVIEW다. 해당 검증 성공과 증거 없이는 DONE이 아니다. 통합·필요한 배포·Smoke Test·문서 갱신도 Task로 추적한다.
- 새로운 필수 작업은 ID·의존성·난이도를 추가한 후 실행한다. 한 Task가 막혀도 독립 READY 작업은 계속한다.

## 3. 모델과 서브에이전트

Scoped feature의 난이도 결정, 첫 위임 또는 실패 승격 시 [agent-model-routing.md](references/agent-model-routing.md)를 읽는다. LOW/LIGHT/low, MEDIUM/STANDARD/medium, HIGH/ADVANCED/high, CRITICAL/PREMIUM/high가 기본이며 Luna/Terra/Sol/Astra는 후보 계열이다. 실제 도구·역할의 지원 모델과 effort를 확인하고 선택 근거와 적용값을 기록한다. 직접 구현하는 Scoped feature도 계획에 난이도·목표 tier/effort와 현재 실행값 또는 선택 불가를 기록한다. 모델 전환만을 위해 불필요한 agent를 만들지 않는다. 선택 불가 시 분할·리뷰로 보완하고 계속한다.

설치된 역할을 명시한다. OMX 일반 구현은 executor, worker는 활성 team 전용이다. 모델 override와 역할 고정이 충돌하면 역할 제약을 따른다. 네이티브 도구가 없으면 같은 소유권 순서로 직접 수행하고 병렬 실행했다고 보고하지 않는다. 파일 기반 handoff를 기본으로 하며 전체 대화 복사는 피한다.

모드와 관계없이 위임할 때 [task-handoff.md](templates/task-handoff.md)의 역할·요구사항·소유권·입출력·검증·완료 기준을 전달한다. Scoped feature는 존재하는 계획/디자인 경로만 전달하고 handoff 때문에 PROGRESS나 MASTER_PLAN을 새로 만들지 않는다.

## 4. 통합·검증·배포

실제 UI·이미지를 변경할 때만 [ui-workflow.md](references/ui-workflow.md)를 반드시 읽는다. 기존 이미지 확인·출처·디자인 일관성·독립 리뷰·실제 UI 조작·여러 화면 크기의 스크린샷 검증을 적용한다.

통합·target 환경 검증을 준비할 때 [validation-and-deployment.md](references/validation-and-deployment.md)를 읽는다. 구현자와 위험 작업 리뷰어를 분리하고 실제 diff를 검토한다. 요청 맥락과 저장소에서 target 검증 필요성을 스스로 판단한다. 승인된 개발환경이 확인되면 별도의 “배포·Smoke Test” 문구 없이 local validation → development deployment → integration → Smoke Test → documentation sync를 수행한다. 대상이나 권한을 특정할 수 없으면 필요한 정보만 묻고, 외부 접근 불가 시 증거와 재개 조건을 BLOCKED로 남기며 다른 작업을 계속한다.

## 5. 종료와 보고

필수 구현·테스트·빌드·통합·요청된 target 검증·Smoke Test·문서 동기화가 충족돼야 완료다. 해당하지 않는 단계는 이유를 기록한다. 누락되거나 BLOCKED인 필수 작업이 있으면 100%/완료를 선언하지 않는다.

milestone마다 결과·진행 중 영역·blocker를 짧게 알린다. 최종 보고는 사용자 언어로 Overall Progress, Completed, Not Completed, Validation Results, Deployment Result, Smoke Test Result, Known Issues, Important Files, How to Continue를 포함한다. 개발환경 가이드가 있으면 경로를 명시한다. 작은 작업은 해당 항목만 간결히 보고한다.
