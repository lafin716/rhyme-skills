# rhyme-skills

개인 에이전트 스킬 모음.

## Skills

| Skill | 설명 |
|-------|------|
| [rhymework](skills/rhymework/SKILL.md) | 소프트웨어 빌드 요청을 자율적으로 계획·분해·병렬 실행·검증까지 수행 (`/rhymework`) |
| [upload-git](skills/upload-git/SKILL.md) | 작업 트리 수정사항을 검토해 비밀 값·산출물을 거르고, 검증 후 논리 단위로 커밋·푸시 (`/upload-git`) |
| [make-release](skills/make-release/SKILL.md) | 커밋·검증 → 버전 파일 일괄 갱신 → 태그 푸시 → Release 워크플로 대기 → 릴리즈 노트 작성·공개 (`/make-release [버전\|patch\|minor\|major]`) |
| [show-link](skills/show-link/SKILL.md) | 스크린샷·파일을 갤러리로 띄워 localhost·LAN·Tailscale 링크로 공유 (`/show-link`, macOS·Linux, `python3` 필요) |
| [show-dev](skills/show-dev/SKILL.md) | 개발 서버를 0.0.0.0에 바로 띄워 LAN·Tailscale(`*.ts.net`·100.x) 주소로 열기 — 허용 호스트 설정 자동 추가 (`/show-dev`, macOS·Linux) |
| [release-show](skills/release-show/SKILL.md) | make-release로 릴리즈를 공개한 뒤 이어서 show-dev로 개발 서버를 LAN·Tailscale 주소로 열기 (`/release-show [버전] [-- show-dev 인자]`) |

## 설치

플러그인으로 설치하면 Claude Code에서는 `/rhyme-skills:<skill>` 이름으로도 호출된다. 같은 이름의 스킬이 `~/.claude/skills/`나 프로젝트 `.claude/skills/`에 있으면 그쪽이 `/<skill>`을 차지하므로, 프로젝트 전용 절차(예: 특정 저장소의 릴리즈 방식)는 프로젝트 스킬이나 CLAUDE.md에 두면 된다.

### Claude Code (plugin)

```bash
claude plugin marketplace add lafin716/rhyme-skills
claude plugin install rhyme-skills@rhyme
```

업데이트:

```bash
claude plugin marketplace update rhyme
claude plugin update rhyme-skills@rhyme
```

### 여러 에이전트에 한 번에 (skills CLI)

Claude Code·Codex 등 여러 에이전트를 함께 쓰면 이 방식 하나로 관리하는 것을 권장한다. Claude Code에 플러그인과 skills CLI를 둘 다 설치하면 같은 스킬이 두 번(`/upload-git`, `/rhyme-skills:upload-git`) 잡히므로 한쪽만 쓴다.

```bash
npx skills@latest add lafin716/rhyme-skills -g -s '*' -y -a claude-code codex  # 필요한 에이전트 나열
```

프로젝트 단위로만 설치하려면 `-g`를 뺀다:

```bash
npx skills@latest add lafin716/rhyme-skills -a <agent>  # claude-code, cursor, opencode, codex, windsurf, amp ...; omit -a to choose
```

업데이트:

```bash
npx skills@latest update -g upload-git show-link show-dev make-release release-show rhymework  # 이 저장소 스킬만
npx skills@latest update -g                                               # 전역 스킬 전부
```

## 릴리스 (maintainer)

스킬을 수정하면 `.claude-plugin/plugin.json`의 `version`을 올린 뒤 push한다. 버전이 같으면 `claude plugin update`가 변경을 감지하지 못한다.

- patch (`0.1.0 → 0.1.1`): 문구 수정, 버그 수정
- minor (`0.1.x → 0.2.0`): 스킬 추가, 동작 변경

## License

[MIT](LICENSE)
