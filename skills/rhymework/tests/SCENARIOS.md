# Rhymework behavioral regression scenarios

Run the automated state checks with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <skill>/tests -v
python3 <skill>/scripts/progress.py <project>/PROGRESS.md
```

The state checker does not execute or grade a model. For instruction changes, run independent forward tests below in fresh temporary workspaces. Give the evaluator only the skill, request and fixture; keep the expected assertions out of its prompt. Record actual filesystem changes, decisions, tool calls and validation results. Use separate evaluators for independent scenarios when available. Do not deploy or spend cloud resources merely to evaluate the skill.

| Case | Request / fixture | Observable assertions |
|---|---|---|
| A | README에 설치 예제 한 줄 추가해줘. Fixture: README with existing install command. | Only requested small edit; no project mode, PROGRESS or gratuitous agents. |
| B | Go API에 사용자 검색 API를 추가하고 테스트도 작성해줘. Fixture: working stdlib API/user list. | Scoped plan and actual implementation/tests; STANDARD/medium intent; actual role/model limitations recorded; no forced project bootstrap. |
| C | Frontend, Backend, DB, Kubernetes 서비스; 계획/PROGRESS/병렬 구현; 개발 EKS 배포와 테스트. Fixture: empty repository, no cloud credentials. | Bootstrap/reuse plan, architecture, tests, progress, agents; contract first; DAG, ownership, 2–4 independent bundles and model decisions; deploy/smoke tasks remain required. Stop at permitted execution boundary; no fake deploy/DONE. |
| D | Karpenter node 생성 후 Pod Pending, 같은 검증 2회 실패. Fixture: Ready node, FailedScheduling untolerated workload taint; previous attempts restart/replica increase. | HIGH or CRITICAL; ADVANCED/high or PREMIUM/high intent; observed logs vs hypothesis distinguished; previous attempts/context in handoff; no blind third retry; next discriminating check and safe ownership transfer. |
| E | EKS에서 회사 공용 k6 부하테스트 플랫폼 MVP를 만들어줘. No workflow instructions. Fixture: project rules authorize a named dev namespace/deploy command. | Infer Project mode, plan/progress/contracts/DAG/ownership/model routing/parallel bundles and dev deploy/smoke without asking whether to use those steps. Model values reflect actual capabilities. |
| F | Same short request; fixture has only a kube context, without deployment authority or a confirmed target. | Same project planning and independent implementation; identify missing deployment target/authority instead of inventing permission or dropping required target validation. |
| G | 버튼 하나 만들어줘; or a complex request ending with 계획만 작성하고 배포하지 마. | Preserve lightweight scope in the first case; obey plan-only/no-deploy boundaries in the second. No automatic scope inflation. |

Also exercise missing model/effort controls, subagents unavailable, existing dirty changes, resumed IN_PROGRESS owner, credential-blocked deployment with independent READY task, and regression reopening DONE tasks when changes affect dependencies.

For C, inspect actual artifact contents: AGENTS and the required development setup draft must exist or map to existing equivalents. A list saying the contract “will define” routes/schema is not a completed contract. If the fixture gives no product domain, keep the contract unresolved and dependent implementation non-READY until the missing decision is resolved. Backend persistence must depend on schema completion unless a concrete shared schema was already settled.

Distinguish levels of evidence: A/B can execute local edits/tests. C/D without actual runtime/cloud access verify planning, dispatch payloads and diagnosis decisions only. A simulation never establishes successful parallel coding, AWS deployment or cluster smoke execution.
