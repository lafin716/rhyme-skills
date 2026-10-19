---
name: upload-git
description: 작업 트리의 수정사항을 전부 검토해 논리 단위로 git 커밋하고 원격에 푸시한다. "/upload-git", "전부 커밋하고 푸시", "깃에 올려줘", "commit and push everything" 같은 요청에 사용.
argument-hint: "[커밋 범위·메시지 힌트 (선택)]"
---

# upload-git — 수정사항 전부 커밋 후 푸시

인자: `$ARGUMENTS` (있으면 커밋 범위·메시지 힌트로 쓴다)

사용자가 이 스킬을 호출한 것 자체가 **현재 브랜치에 커밋하고 푸시하라는 승인**이다(기본 브랜치 포함). 단, 아래 "멈출 때"에 해당하면 진행하지 말고 보고한다. 프로젝트 지침(CLAUDE.md·AGENTS.md·CONTRIBUTING.md)에 커밋·브랜치 규칙이 있으면 그 규칙이 이 문서보다 우선한다.

## 절차

1. **상태 파악** (병렬로)
   - `git status --short`, `git diff --stat`, `git diff`, `git diff --cached`
   - `git log --oneline -10` — 커밋 메시지 언어·접두사(`feat:`, `fix:`, `chore:` 등) 관례 확인
   - `git remote -v`, `git status -sb` — 현재 브랜치·upstream·ahead/behind
   - 추적되지 않은 파일(`??`)은 내용을 확인한다. 폴더째 추적 안 된 경우 안의 파일 목록까지 본다.
   - 진행 중인 merge·rebase·cherry-pick(`.git/MERGE_HEAD`, `.git/rebase-merge` 등)이나 detached HEAD면 멈추고 보고한다.
   - 서브모듈 변경(`git submodule status`의 `+`)이 있으면 서브모듈 자체는 건드리지 않고 포인터 변경만 커밋 대상으로 판단한다.

2. **커밋에 넣으면 안 되는 것 걸러내기**
   - 비밀 값: `.env*`(`.env.example` 류 제외), API 키·토큰·인증서·개인키(`*.pem`, `id_rsa*`, `*.p12`, `*.keystore`), `*secret*`, `credentials*`, `identity.json` 등. diff에서 키처럼 보이는 문자열(`sk-…`, `ghp_…`, `AKIA…`, `-----BEGIN … PRIVATE KEY-----`)도 확인한다.
   - 임시·산출물: `test-results/`, `playwright-report/`, `coverage/`, 빌드 결과(`dist/`, `build/`, `release/`, `target/`), `node_modules/`, `__pycache__/`, `.DS_Store`, 디버그용 임시 spec·스크립트, 큰 바이너리(수 MB 이상).
   - 이런 파일은 커밋하지 않고 보고한다(필요하면 `.gitignore` 추가를 제안만 한다).

3. **검증** — 프로젝트 지침·`package.json` scripts·Makefile 등에 정해진 검증 명령이 있으면 실행한다(예: `pnpm typecheck && pnpm lint && pnpm test`, `make test`, `cargo test`). 이번 대화에서 **같은 작업 트리 상태로** 이미 통과했다면 생략하고 그 사실을 보고에 적는다. 검증 명령이 없으면 생략하고 그렇게 적는다. 실패하면 커밋하지 않고 보고한다.

4. **논리 단위로 나눠 커밋**
   - 서로 다른 기능·수정이 섞여 있으면 기능별로 파일을 나눠 `git add <경로들>` → 커밋을 반복한다. 한 파일이 여러 기능에 걸치면 그 파일은 주된 기능 쪽에 넣는다(`git add -p` 같은 대화형 명령은 쓰지 않는다).
   - `git add -A`보다 경로를 명시해 스테이징한다(2단계에서 거른 파일 제외). 사용자가 미리 스테이징해 둔 것이 있으면 그 묶음을 첫 커밋으로 존중한다.
   - 메시지: 저장소 관례의 언어·접두사를 따른다(관례가 없으면 사용자 언어로 명령형 한 줄). 제목 한 줄 요약 + 필요하면 본문 글머리표. HEREDOC(`git commit -F - <<'EOF'`)으로 작성한다. 셸이 HEREDOC을 지원하지 않으면(Windows PowerShell) 메시지를 BOM 없는 UTF-8 파일로 쓰고 `git commit -F <파일>`.
   - 대화에서 지정된 attribution 줄(예: `Co-Authored-By: ...`)이 있으면 메시지 끝에 붙인다.
   - 훅 실패 시 원인을 고친 뒤 **새 커밋**을 만든다(`--amend`, `--no-verify` 금지). 훅이 파일을 자동 수정했으면 그 수정분을 다시 스테이징해 커밋한다.

5. **푸시**
   - upstream이 있으면 `git push`, 없으면 `git push -u origin <현재 브랜치>`(원격이 `origin`이 아니면 유일한 원격 또는 upstream 원격을 쓴다).
   - 거부(non-fast-forward)되면 `git pull --rebase`로 통합을 시도하고, 충돌이 나면 `git rebase --abort`로 되돌린 뒤 멈추고 보고한다. **force push 금지.**
   - 보호 브랜치 거부(protected branch, PR 필요)면 멈추고 새 브랜치로 푸시할지 사용자에게 묻는다.

6. **확인·보고** — `git status -sb`로 작업 트리가 깨끗하고 ahead 0인지 확인한 뒤, 사용자 언어로 짧게 보고한다:
   - 만든 커밋 목록(해시 + 제목), 푸시된 원격/브랜치 범위(`old..new`)
   - 검증 결과(실행/생략 이유), 커밋에서 제외한 파일과 이유

## 멈출 때 (커밋·푸시하지 않고 보고)
- 비밀 값으로 보이는 내용이 변경에 포함되어 분리할 수 없을 때
- 검증 실패, 병합 충돌, rebase 충돌, 진행 중인 merge/rebase, detached HEAD
- 원격이 없거나 인증 실패, 보호 브랜치 거부
- 변경 사항이 없을 때 → "커밋할 변경이 없습니다"라고 알리고, ahead 커밋이 있으면 푸시만 한다
