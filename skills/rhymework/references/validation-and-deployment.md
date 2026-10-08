# 통합, target 환경 검증, 종료

## 검증 계약

Task 배정 전에 실행할 명령, 환경, 관찰할 결과를 TEST_STRATEGY/Task contract에 정한다. 단위/통합 테스트, build, lint, typecheck, helm template, manifest validation, 실제 deployment, UI 조작 중 해당 작업을 증명하는 검사를 선택한다. 코드가 바뀌면 영향받은 증거를 갱신한다. 명령/결과/시각/코드 revision 또는 snapshot/로그 경로를 보관하며 secret은 제거한다.

구현 에이전트는 검증을 실행해 결과를 보고하고 리더는 실제 diff·출력과 수용 기준을 확인한다. 단순 PASS 문자열, agent의 자신감, 예전 코드의 테스트 성공은 완료 증거를 대체하지 않는다. 독립 통합 Task는 합쳐진 코드에서 검증한다.

## 독립 리뷰

기존 여러 화면 UI 작업의 독립 리뷰를 유지한다. Authentication/Authorization, RBAC/IAM/IRSA, raw script execution, network policy, compiler/state machine, DB migration, infrastructure는 위험에 맞는 별도 reviewer를 둔다. ADVANCED/high 후보로 구현했다면 별도 ADVANCED/high reviewer, 프로젝트 전체 최종 리뷰는 PREMIUM/high를 우선하되 실제 모델 지원을 따른다.

리뷰어는 먼저 bug, missing test, security risk, contract violation, race, integration/operational risk를 찾는다. 전체 코드를 다시 작성하지 않는다. 리더가 지적을 Task/수정에 연결하고 관련 검증 후 닫는다. 실제 reviewer가 없으면 독립 리뷰를 실행했다고 보고하지 않는다.

## Target 환경

계획에서 로컬/개발 서버/cluster, 계정·region·namespace·서비스 주소, 접근 방법, 배포 범위, 검증 책임자를 식별한다. 사용자가 “로컬에서는 어렵고 개발 서버에서 테스트”라고 하면 이를 따른다. 로컬 완전 재현을 새 필수 과제로 만들지 않는다.

“만들어줘”에는 결과를 증명하는 테스트·Smoke 설계도 포함한다. “EKS에서 사용할 플랫폼”처럼 target이 결과의 일부이거나, 기존 프로젝트 지침에서 개발 배포를 완료 조건으로 정했다면 배포·target integration·Smoke를 자동으로 계획에 포함한다. 세션의 기존 권한과 신뢰할 수 있는 프로젝트 운영 지침이 특정 개발 대상의 배포를 허용하고 대상/명령/접근이 확인되면, 사용자가 매번 “배포하고 Smoke Test”라고 쓰지 않아도 실행한다. kube context나 credential의 존재만으로 외부 변경 권한을 추론하지 않는다. 운영 배포, 새로운 유료 인프라 생성, 파괴적 migration은 일반적인 “만들어줘”에서 임의로 승인된 것으로 취급하지 않는다.

로컬 도구처럼 외부 배포가 필요 없는 결과는 적절한 로컬 실행/Smoke로 검증한다. 개발 대상이 불명확하면 먼저 기존 문서·config·배포 스크립트를 확인하고 해결되지 않는 대상/권한만 질문한다. 그동안 독립적인 구현·검증·문서는 계속한다.

1. 가능한 local validation: build/unit/lint/typecheck/manifest 검증.
2. 요청과 권한으로 특정된 development target을 확인하고 배포 artifact/revision, config/secret reference, migration 순서, rollback 경로를 기록한다.
3. 기존 배포 명령을 실행하고 rollout/health를 실제 관찰한다. 개발 배포 요청은 그 범위에서 계속 실행할 권한이다. 사용자가 이미 승인한 범위의 확인을 반복하지 않는다. 다른 계정/운영 환경/파괴적 migration으로 범위가 바뀌거나 권한이 없으면 필요한 결정만 요청한다.
   이 범위는 식별된 non-production account/cluster/namespace, 검토한 명령과 테스트 데이터, 비파괴적 rollout을 뜻한다. 대상이 불명확하면 저장소 설정과 접근 정보를 먼저 확인하고, 여전히 대상을 특정할 수 없을 때만 질문한다.
4. 실제 endpoint/namespace에서 integration과 Smoke를 실행한다. health 외에 대표 사용자 흐름·의존 서비스·권한/실패 처리 중 MVP 수용 기준을 증명한다. 테스트 데이터·부하 한도·cleanup도 정한다.
5. 실패 시 로그를 수집하고 영향 범위에 맞는 rollback 또는 수정 후 재검증을 수행한다. 데이터 손실 가능한 rollback을 추측해 실행하지 않는다.
6. 실제 차이와 결과를 개발환경 가이드·TEST_STRATEGY·MASTER_PLAN·PROGRESS에 반영한다.

Credential 없음, AWS 권한 부족, cluster 접근/VPN/외부 승인/secret 누락은 정상 BLOCKED다. 실패 증거, 영향 Task, 해제 조건을 적고 독립 작업은 계속한다. 구현 난이도·파일 수·소요 시간은 BLOCKED 이유가 아니다. 이를 분할/승격한다. 외부 환경에 대한 증거가 없으면 simulated/static 결과를 실제 배포 성공으로 표시하지 않는다.

## 완료 및 최종 보고

필수 구현·테스트·빌드·통합·필요한 target 검증·Smoke·문서 sync·최신 PROGRESS와 Known Issues가 모두 확인돼야 전체 완료다. 검증 불가 필수 항목은 BLOCKED/미완료이며 단순 N/A로 제외하지 않는다. 실제로 해당하지 않는 단계만 계획에 근거를 남겨 제외한다. 범위 변경은 이유와 사용자 권한을 보존하고 완료율을 높이기 위해 필수 Task를 지우지 않는다.

최종 답변 항목:
- Overall Progress: 계산 방식과 수치.
- Completed / Not Completed: 기능과 blocker.
- Validation Results: 명령과 실제 결과/증거.
- Deployment Result / Smoke Test Result: target·revision·결과 또는 미실행 사유.
- Known Issues: 남은 위험과 영향.
- Important Files: 계획, progress, 검증 기록, setup guide.
- How to Continue: 다음 READY/해제 조건/재개 순서. 가이드가 있으면 “개발 서버 구축·재배포는 docs/DEV_SERVER_SETUP.md를 먼저 확인”이라고 안내한다.
