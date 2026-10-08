# rhyme-skills

개인 에이전트 스킬 모음.

## Skills

| Skill | 설명 |
|-------|------|
| [rhymework](skills/rhymework/SKILL.md) | 소프트웨어 빌드 요청을 자율적으로 계획·분해·병렬 실행·검증까지 수행 (`/rhymework`) |

## 설치

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

### 기타 에이전트 (skills CLI)

```bash
npx skills@latest add lafin716/rhyme-skills -a <agent>  # claude-code, cursor, opencode, codex, windsurf, amp ...; omit -a to choose
```

업데이트:

```bash
npx skills@latest update
```
