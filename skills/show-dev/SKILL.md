---
name: show-dev
description: 현재 저장소의 개발 서버를 Tailscale 주소(MagicDNS *.ts.net · 100.x IP)로 열어 휴대폰·다른 PC에서 접속하게 한다. Tailscale 상태는 하루 단위로 캐시하고, 프론트엔드의 허용 호스트(allowedHosts·allowedDevOrigins·ALLOWED_HOSTS 등) 설정을 소스에 추가해 "허용되지 않은 호스트" 오류를 막는다. Tailscale이 없거나 꺼져 있으면 진행하지 않고 다른 방법을 추천한다. "/show-dev", "개발서버 외부에서 접속", "폰에서 개발환경 열어줘", "dev 서버 링크" 같은 요청에 사용.
argument-hint: "[앱 경로·스크립트 이름·포트 (선택)]"
---

# show-dev — 개발 서버를 Tailscale 주소로 열기

인자: `$ARGUMENTS` (모노레포의 앱 경로, 실행할 스크립트, 포트 등 힌트)

Tailscale tailnet 안의 내 기기에서만 열리는 비공개 주소가 기본이다. 공개 인터넷 노출(`tailscale funnel`, cloudflared, ngrok 등)은 사용자가 명시적으로 원할 때만 한다.

스크립트: 이 스킬 폴더의 `scripts/show-dev.sh` (Claude Code에서는 `${CLAUDE_SKILL_DIR}/scripts/show-dev.sh`). 아래에서는 `show-dev.sh`로 줄여 쓴다. macOS·Linux에서 `bash`·`curl`·`python3`가 필요하다. 프레임워크별 수정 방법은 [references/frameworks.md](references/frameworks.md).

## 1. Tailscale 확인 (하루 캐시)
`show-dev.sh check` 실행.
- 성공 결과는 `~/.cache/show-dev/tailscale.env`에 **오늘 날짜**로 캐시되어, 같은 날에는 tailscale을 다시 호출하지 않는다(`(cached YYYY-MM-DD)` 표시). 실패는 캐시하지 않아 사용자가 Tailscale을 켜면 바로 반영된다.
- 사용자가 "Tailscale 다시 확인", 기기 이름 변경, 또는 7단계 검증에서 Tailscale 주소만 응답이 없으면 `show-dev.sh check --refresh`.
- **exit 2(missing/stopped)면 여기서 멈춘다** — 소스 수정·서버 실행을 하지 않고, 이유와 함께 대안을 추천한다:
  1. Tailscale 켜기/설치: macOS `open -a Tailscale`(없으면 `brew install --cask tailscale` 또는 App Store), Linux `sudo tailscale up`(없으면 `curl -fsSL https://tailscale.com/install.sh | sh`). 휴대폰에도 Tailscale 앱으로 같은 계정 로그인. 켠 뒤 다시 `/show-dev`.
  2. 같은 Wi-Fi라면 LAN 주소(`http://<LAN IP>:<포트>`) — 개발 서버를 `0.0.0.0`에 바인딩하면 된다.
  3. 공개 터널(인터넷 누구나 접근 가능 — 명시적 동의 필요): `cloudflared tunnel --url http://localhost:<포트>`(계정 불필요), `ngrok http <포트>`, VS Code/Cursor 포트 포워딩. 이 경우 허용 호스트에 `.trycloudflare.com`·`.ngrok-free.app` 등을 추가해야 한다.
  - 사용자가 대안 중 하나를 고르면 그 방법으로 진행한다(2~7단계를 해당 도메인으로 적용).

## 2. 개발 환경 파악
- 실행 대상: 인자 → 대화에서 작업 중인 앱 → 저장소 루트 순. 모노레포(`pnpm-workspace.yaml`, `turbo.json`, `apps/*`)에서 대상이 여러 개고 정할 수 없으면 한 번 묻는다. 프론트+API처럼 함께 떠야 하는 구성이면 둘 다 대상이다.
- 프레임워크·버전: `package.json` 의존성과 설정 파일(`vite.config.*`, `next.config.*`, `nuxt.config.*`, `astro.config.*`, `angular.json`, `vue.config.js`, `webpack.config.*`, `svelte.config.*`), 백엔드(`manage.py`/`settings.py`, `config/environments/development.rb`, `artisan`, `pyproject.toml`, `go.mod` 등).
- 실행 명령: 프로젝트 지침(CLAUDE.md·AGENTS.md·README)에 개발 서버 실행법이 있으면 그것, 없으면 `package.json` scripts의 `dev` → `start` → `serve`. 패키지 매니저는 lockfile로 고른다. 포트는 설정·스크립트·기본값으로 예상하고 실행 로그로 확정한다.
- 이미 떠 있는지: `lsof -nP -iTCP -sTCP:LISTEN | grep -E ':<포트>\b'` — `127.0.0.1`/`localhost`에만 바인딩돼 있으면 설정 수정 후 재시작이 필요하다.

## 3. 허용 호스트·바인딩 소스 작업
[references/frameworks.md](references/frameworks.md)에서 해당 프레임워크 절을 따라 수정한다. 원칙:
- **바인딩**: `0.0.0.0`(또는 프레임워크의 `host: true`)으로 열어 외부 인터페이스에서 받게 한다.
- **허용 호스트**: Tailscale 도메인 전체 `.ts.net`(하위 도메인 포함 표기)을 추가한다. 해당 프레임워크가 IP도 검사하면 Tailscale IP(`check`의 `ip`)도 넣는다. `allowedHosts: true`/`'all'`·`ALLOWED_HOSTS = ['*']`처럼 검사를 끄는 설정은 사용자가 원할 때만.
- **기존 값과 병합**한다(배열에 추가, 중복 없이). 이미 들어 있으면 수정하지 않는다(멱등).
- **개발 전용 범위**에만 넣는다(dev server/preview 설정, development 설정 파일). 프로덕션 빌드·배포 설정에 영향을 주지 않는다.
- **연결 문제도 함께 확인**: 프론트가 `http://localhost:<API포트>`를 하드코딩해 API를 부르면 휴대폰에서는 휴대폰 자신의 localhost로 가서 실패한다 → dev proxy(상대 경로)로 바꾸거나 개발용 env를 `window.location.hostname` 기반으로. 다른 포트의 API를 직접 부르면 백엔드 CORS에 `*.ts.net` origin 허용(개발 전용). 백엔드가 dev 서버 자산을 `localhost` URL로 넣는 구성(Laravel·Rails+Vite 등)은 HMR/자산 호스트를 Tailscale 이름으로.
- 수정은 커밋하지 않는다(사용자가 원하면 upload-git). 무엇을 왜 바꿨는지 보고한다.

## 4. 서버 실행
- 이미 떠 있고 바인딩·설정이 맞으면 재사용한다(Vite 등은 설정 파일 변경 시 자동 재시작 — 로그로 확인, Next.js·백엔드는 재시작 필요).
- 새로 띄울 때는 **백그라운드**로: Claude Code는 Bash `run_in_background`, 그 외는 `nohup <명령> > "${TMPDIR:-/tmp}/show-dev-<저장소>-<포트>.log" 2>&1 &`로 PID와 로그 경로를 기록한다. 설정으로 바인딩을 못 바꾸는 도구는 실행 인자로 준다(예: `pnpm dev --host 0.0.0.0`, `npm run dev -- --host 0.0.0.0`, `next dev -H 0.0.0.0`, `rails s -b 0.0.0.0`, `uvicorn ... --host 0.0.0.0`).
- 로그에서 실제 포트·에러를 확인한다(포트가 이미 쓰이면 다른 포트로 올라갈 수 있다).

## 5. 검증
`show-dev.sh verify <포트> [경로]` — localhost, Tailscale 도메인(Host 헤더, Tailscale IP로 고정 해석), Tailscale IP로 각각 요청해 응답 코드와 "Blocked request"/"Invalid Host header"/`DisallowedHost` 같은 허용 호스트 오류를 검사한다.
- BLOCKED면 3단계 설정을 고치고(서버 재시작 필요 여부 확인) 다시 검증한다. 같은 방식으로 두 번 실패하면 서버 로그와 설정을 보고하고 멈춘다.
- Next.js는 페이지는 200이어도 `/_next/*`·HMR이 막힐 수 있다 → 서버 로그에 `Cross origin request detected`·`Blocked cross-origin request` 경고가 없는지 확인한다.
- API까지 쓰는 화면이면 API 경로도 Tailscale 도메인으로 한 번 확인한다(`verify <API포트> /health` 또는 프록시 경로).
- 가능하면 브라우저 자동화(Playwright 등)로 `http://<Tailscale DNS>:<포트>`를 열어 콘솔 에러·빈 화면이 없는지 본다(필수 아님).

## 6. 보고
사용자 언어로 짧게:
- 접속 URL: `show-dev.sh urls <포트> [경로]` 출력 그대로 — localhost · LAN · Tailscale(MagicDNS 이름 · 100.x IP)
- 바꾼 파일과 이유(허용 호스트·바인딩·프록시/CORS), 커밋하지 않았다는 사실
- 검증 결과, 서버 로그 경로와 종료 방법(백그라운드 작업 중지 또는 `kill <PID>`)
- 참고: 다른 기기에도 Tailscale 앱이 같은 tailnet으로 로그인돼 있어야 열린다. `http://*.ts.net`은 보안 컨텍스트가 아니어서 Service Worker·카메라·클립보드·`crypto.subtle` 등이 막힌다 — 필요하면 HTTPS로 `tailscale serve --bg <포트>`(tailnet 전용, 관리 콘솔에서 HTTPS 인증서 활성화 필요, 끄기는 `tailscale serve reset`)를 제안한다(Tailscale 설정을 바꾸므로 사용자 확인 후 실행). 이 경우 허용 호스트는 그대로 `.ts.net`으로 충분하다.
