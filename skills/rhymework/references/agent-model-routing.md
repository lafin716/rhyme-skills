# Agent Model Routing

Rhymework는 모델 라우팅을 신뢰성과 비용 균형을 맞추는 수단으로 사용한다. 아래 모델 계열명은 하드코딩된 요구가 아니라 권장 매핑이다. 현재 Codex 환경에서 실제로 사용할 수 있는 role, model, reasoning effort를 확인하고, 요청값과 실제로 보이는 실행값을 정직하게 기록한다.

## 난이도 분류

각 task는 배정 전에 분류한다. 새 증거가 나오면 다시 분류한다.

| Complexity | 판단 기준 | Logical tier | 기본 reasoning |
|---|---|---|---|
| LOW | 요구가 명확하고 작으며 반복 패턴이고 실패 영향이 작다. README, boilerplate, 단순 UI 문구, lint fix, 기존 패턴의 작은 CRUD. | LIGHT | low |
| MEDIUM | 일반적인 제품 구현이며 저장소 패턴이 분명하다. Go CRUD API, Nuxt page, repository, migration, 일반 Kubernetes manifest, API integration, 일반 integration test. | STANDARD | medium |
| HIGH | 설계 판단, 어려운 디버깅, 여러 subsystem 계약이 필요하다. state machine, compiler, complex business rule, Kubernetes controller, Karpenter, IRSA, RBAC, ESO, distributed execution, 복잡한 integration failure. | ADVANCED | high |
| CRITICAL | architecture, security, 운영 배포, multi-agent integration 방향에 영향을 준다. 최종 contract, cross-system RCA, authorization/security review, deployment review, architecture change, project-wide integration review. | PREMIUM | high, 매우 어려운 경우만 xhigh |

여러 행에 걸치면 보안, 데이터 무결성, 외부 운영, 배포, 여러 agent에 영향을 주는 쪽을 우선해 더 높은 등급을 선택한다.

## 권장 모델 계열

먼저 logical tier를 고르고, 그 다음 현재 사용 가능한 모델에 매핑한다.

| Logical tier | 권장 계열 | 기본 용도 |
|---|---|---|
| LIGHT | Luna | LOW 구현과 기계적인 후속 작업 |
| STANDARD | Terra | MEDIUM 기능 구현과 일반 테스트 |
| ADVANCED | Sol | HIGH 구현, infra, compiler, 어려운 debugging |
| PREMIUM | Astra | CRITICAL architecture, integration, review, incident analysis |

Luna, Terra, Sol, Astra는 권장 계열명이다. 환경마다 concrete model, role prompt, specialist 기본값이 다를 수 있다. 정확한 계열이 없으면 가장 가까운 지원 옵션을 고른다. 예: Astra가 없고 Sol만 있으면 Sol/high로 실행하고 분할·리뷰를 강화한다. role만 선택 가능하면 role을 사용하고, 그 role의 고정 모델 또는 관찰된 기본값을 기록한다.

확인 순서: 현재 호출 도구의 schema/지원 목록 → 설치된 role의 제약 → 사용자가 제공한 설정 → 로컬 모델 cache(참고용). cache에만 있는 모델을 지원한다고 가정하지 않는다. 선택한 모델이 요청 effort를 지원하는지 따로 확인하고, 미지원이면 지원되는 가장 가까운 effort 또는 관찰된 기본값을 사용한다. xhigh 이상의 최대 effort는 매우 어려운 문제이고 해당 표면이 지원할 때만 근거를 남겨 사용한다.

## 현재 Codex 제약

- full-history native subagent fork는 parent model과 reasoning effort를 상속한다. full-history fork에서는 model 또는 reasoning override를 요청하지 않는다.
- model/effort override가 필요하고 도구가 지원하면 file-based handoff를 사용하고 `fork_turns=none` 또는 작은 양의 fork history를 사용한다.
- 설치된 role은 자체 model/effort를 고정할 수 있다. `model` 인자를 넣었다고 role 고정값이 반드시 덮인다고 가정하지 않는다.
- effective model을 알 수 없으면 값을 지어내지 말고 `unknown` 또는 `role default observed`처럼 기록한다.
- model 선택 기능이 없으면 task를 더 작게 나누고, handoff 파일을 명확히 만들고, 검증을 강화하고, 위험 작업에 별도 review agent를 붙인다.
- 사용자가 전역 설정 변경을 요청하지 않았다면 Rhymework가 global model config를 자동 변경하지 않는다.

## 배정 규칙

프로젝트 모드에서는 spawn 또는 직접 실행 전에 `PROGRESS.md`에 다음을 기록한다. Scoped feature는 기존 계획/보고에 기록하며 라우팅 때문에 PROGRESS를 새로 만들지 않는다.

- `Complexity`
- `Model`과 `Reasoning`에는 실제 적용값(알 수 없으면 unknown)을 기록하고 요청 tier/effort는 Decisions에 구분한다.
- 선택 이유 한 줄. 가능하면 `Model Decision` note 또는 task 상세에 남긴다.

예:

```text
Task: K6-004
Complexity: HIGH
Model: Sol requested, role default unknown
Reasoning: unknown (requested high)
Reason: Scenario DSL and distributed k6 execution contract affect backend and infra integration.
```

가장 강한 모델이 아니라 해당 task를 안정적으로 끝낼 수 있는 가장 비용 효율적인 옵션을 선택한다.

- 작은 반복 작업은 LIGHT/low.
- 대부분의 일반 구현은 STANDARD/medium.
- 어려운 구현이나 debugging은 ADVANCED/high.
- architecture, integration review, security, 운영 위험은 PREMIUM/high.
- 고난도 설계가 끝난 뒤 반복 구현은 de-escalate한다. 예: Astra/high가 contract를 결정한 뒤 Terra/medium이 CRUD와 fixture test를 구현한다.

## Review 분리

위험 task는 구현과 review를 분리한다. Reviewer에게 plan, contract, diff summary, validation evidence, 남은 불확실성을 전달한다. Reviewer는 bug, missing test, security risk, contract violation, race condition, integration issue, operational risk를 찾는다. Leader가 요청하지 않은 한 처음부터 코드를 다시 작성하지 않는다.

다음 영역은 독립 review를 요구한다.

- authentication, authorization, IAM, IRSA, RBAC, network policy
- raw script execution 또는 user-supplied execution
- data risk가 있는 database migration
- compiler, state machine, scheduler, distributed execution
- infrastructure, Kubernetes, deployment, rollback
- project-wide integration 또는 release readiness

## Escalation

같은 context로 같은 task를 무한 재시도하지 않는다.

다음 조건에서는 escalation을 고려한다.

- 같은 validation이 2회 실패
- 같은 영역을 반복 수정했지만 pass evidence가 없음
- 현재 agent가 원인에 대해 추측만 가지고 있음
- architecture 또는 contract 변경 가능성이 있음
- AWS, Kubernetes, application code처럼 여러 subsystem으로 문제가 확산됨
- security 또는 운영 불확실성이 남음
- bounded attempt 후 confidence가 낮음

기본 승격 경로:

```text
LIGHT/Luna low -> STANDARD/Terra medium -> ADVANCED/Sol high -> PREMIUM/Astra high -> PREMIUM/Astra xhigh only when available and justified
```

상위 agent에게 넘길 때는 처음부터 다시 조사하게 하지 말고 file-based handoff에 다음을 담는다.

- task ID와 원래 요구사항
- `PROGRESS.md`의 현재 상태
- 수정 파일
- 현재 구현 요약
- 정확한 실패 command, test, log, error snippet
- 시도한 해결책과 폐기한 가설
- 현재 최선의 가설과 confidence
- contract, dependency, file ownership 제한

같은 실패의 두 번째 시도 이후에는 같은 처방의 세 번째 시도를 중단하고 로그 기반 원인 분리·task 재분할 또는 다른 tier/reviewer로 전환한다. 이전 작성자가 멈추고 소유권을 반환했는지 확인한 뒤 상위 agent에 배정한다. 총 시도 이력은 재배정 때 초기화하지 않는다. 최상위 모델에서도 새 증거 없는 재시도는 금지하며, 더 작은 재현/진단 Task로 바꿔 진행한다. credential, cluster access, secret, external approval 부족 때문에 진행할 수 없으면 task를 `BLOCKED`로 표시하고 독립적인 READY task를 계속 진행한다.
