# rhyme-skills

개인 Claude Code 스킬 모음.

## Skills

| Skill | 설명 |
|-------|------|
| [rhymework](skills/rhymework/SKILL.md) | 소프트웨어 빌드 요청을 자율적으로 계획·분해·병렬 실행·검증까지 수행 (`/rhymework`) |

## 설치

```bash
git clone https://github.com/lafin716/rhyme-skills.git
cp -R rhyme-skills/skills/rhymework ~/.claude/skills/
```

또는 저장소를 계속 동기화하려면 심볼릭 링크를 사용:

```bash
ln -s "$(pwd)/rhyme-skills/skills/rhymework" ~/.claude/skills/rhymework
```
