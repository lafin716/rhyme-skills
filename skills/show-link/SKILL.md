---
name: show-link
description: 앱/화면 스크린샷(또는 이미지·동영상·파일)을 갤러리 페이지로 띄우고 휴대폰 등 다른 기기에서 열 수 있는 링크(localhost·LAN·Tailscale)로 보여 준다. "/show-link", "스크린샷 찍어서 링크로 보여줘", "외부링크로 보여줘", "폰에서 볼 수 있게" 같은 요청에 사용.
argument-hint: "[보여 줄 화면·파일 (생략 시 직전 작업 화면)]"
---

# show-link — 스크린샷을 찍어 링크로 보여 주기

인자: `$ARGUMENTS`

공개 업로드가 아니라 이 컴퓨터에서 `0.0.0.0`으로 띄우는 비공개 링크다(같은 LAN 또는 Tailscale 기기에서 열림). 인터넷 어디서나 열려야 한다면(imgur·gist 등 공개 업로드) 사용자에게 먼저 확인한다.

스크립트: 이 스킬 폴더의 `scripts/show-link.sh` (Claude Code에서는 `${CLAUDE_SKILL_DIR}/scripts/show-link.sh`). 아래에서는 `show-link.sh`로 줄여 쓴다. macOS·Linux에서 `bash`·`python3`·`curl`이 필요하다.

## 절차

1. **무엇을 보여 줄지 정한다** — 인자나 대화에서 보여 줄 화면·파일을 정한다. 없으면 직전 작업에서 바꾼 화면. 이미 있는 파일(이미지·동영상·PDF·HTML 리포트 등)이면 2단계를 건너뛴다.
2. **스크린샷 찍기** — 작업 폴더 `${TMPDIR:-/tmp}/show-link-src/<이름>-<MMDD-HHMM>/`에 저장한다. 이름은 짧은 영문 kebab-case(예: `hosts-list`).
   - 웹 UI: 프로젝트에 Playwright가 있으면 임시 spec(예: `e2e/zz-shot-<이름>.spec.ts`)을 만들어 필요한 상태(주입 데이터·클릭)를 재현하고 `page.screenshot({ path: \`${process.env.SHOT_DIR}/${info.project.name}-N-<설명>.png\`, fullPage: true })`로 찍는다. 프로젝트의 패키지 매니저로 `SHOT_DIR=<폴더> <pnpm|npm|yarn> exec playwright test <spec>` 실행 후 **임시 spec을 지운다**. 모바일·데스크톱 프로젝트가 있으면 둘 다. Playwright가 없으면 브라우저 자동화 도구(MCP 등)나 `npx playwright screenshot <url> <파일>`을 쓴다. 개발 서버가 필요하면 먼저 띄운다.
   - 데스크톱 앱 창: macOS `screencapture -x -l <windowId> <파일>` 또는 `screencapture -x <파일>`, Linux `gnome-screenshot -f`·`grim`·`import -window root` 중 있는 것.
   - 터미널/CLI 출력: 텍스트 파일로 저장하거나 HTML로 감싸 보여 준다.
   - 찍은 이미지를 직접 열어 보고(Claude는 Read, Codex는 이미지 보기) 의도한 화면인지 확인한다(빈 화면·로딩 중·에러 오버레이면 다시 찍기).
   - 비밀 값(API 키·토큰·페어링 키·개인 정보 등)이 화면에 보이면 링크로 띄우지 않는다.
3. **띄우기** — `show-link.sh <이름> <폴더|파일>...` 실행. 갤러리 `index.html`을 만들고 `python3 -m http.server`(포트 8765, `SHOW_LINK_PORT`로 변경)를 백그라운드로 띄우거나 이미 떠 있으면 재사용한다. 출력된 URL을 그대로 쓴다.
   - 포트 충돌로 실패하면 `SHOW_LINK_PORT=<다른 포트>`로 다시 실행한다.
   - LAN·Tailscale 줄이 없으면 해당 네트워크가 없는 것이다. 지어내지 말고 있는 주소만 알린다.
4. **보고** — 사용자 언어로 짧게:
   - 링크: localhost · LAN · Tailscale(MagicDNS 이름 · 100.x IP) 중 출력된 것 모두
   - 장면별 한 줄 설명(파일 이름 ↔ 화면 내용)
   - 목록: `show-link.sh --list`, 서버 종료: `show-link.sh --stop` (보고에는 실제 경로로 적는다)

다른 기기에서 열리지 않으면 방화벽(macOS: 시스템 설정 → 네트워크 → 방화벽에서 python3 수신 허용)을 확인하라고 안내한다.
