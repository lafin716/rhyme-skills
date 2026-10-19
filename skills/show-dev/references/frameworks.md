# 프레임워크별 허용 호스트·바인딩 설정

`<TS_IP>`는 `show-dev.sh urls` 출력의 Tailscale 100.x IP(Tailscale이 꺼져 있으면 생략). 모든 예시는 **기존 설정에 병합**한다(값이 이미 있으면 배열에 추가). 버전이 오래돼 해당 옵션이 없으면 그 버전에는 호스트 검사가 없는 것이므로 바인딩만 바꾼다 — 설정 키를 지어내지 말고, 확실하지 않으면 설치된 패키지의 타입 정의(`node_modules/<pkg>/**/*.d.ts`)나 문서로 확인한다.

## Vite 계열 (Vite, React/Vue/Svelte + Vite, SvelteKit, SolidStart, React Router v7/Remix-vite, Qwik, Storybook-vite)
`vite.config.*`:
```ts
export default defineConfig({
  server:  { host: '0.0.0.0', allowedHosts: ['.ts.net'] },
  preview: { host: '0.0.0.0', allowedHosts: ['.ts.net'] },
})
```
- `allowedHosts`는 Vite 5.4.12+/6.0.9+에서 검사한다. 앞의 `.`은 하위 도메인 전체. IP 주소·localhost는 기본 허용이라 `<TS_IP>`는 넣지 않아도 된다.
- `server.hmr.host`가 `localhost`로 고정돼 있으면 지운다(기본값은 페이지 호스트를 따른다).
- 설정이 함수형(`defineConfig(({ mode }) => ({...}))`)이면 반환 객체에 넣는다. 프레임워크 래퍼가 vite 설정을 감싸면 아래 해당 절을 본다.
- API 프록시: `server.proxy: { '/api': 'http://localhost:<API포트>' }` + 프론트는 상대 경로 `/api`.

## Next.js
`next.config.*`:
```js
const nextConfig = { allowedDevOrigins: ['*.ts.net'] }
```
- 15.2+에서 dev 리소스(`/_next/*`, HMR)의 교차 출처 접근을 검사한다(16부터 기본 차단). 와일드카드 `*.ts.net` 지원. IP로도 접속하면 `'<TS_IP>'`도 추가.
- 바인딩: `next dev`는 기본으로 모든 인터페이스에서 듣는다. 스크립트에 `-H localhost`/`--hostname 127.0.0.1`이 있으면 `-H 0.0.0.0`으로.
- next.config 변경은 서버 재시작 필요.

## Nuxt 3/4
`nuxt.config.ts`:
```ts
export default defineNuxtConfig({
  devServer: { host: '0.0.0.0' },
  vite: { server: { allowedHosts: ['.ts.net'] } },
})
```

## Astro
`astro.config.*`:
```js
export default defineConfig({
  server: { host: true, allowedHosts: ['.ts.net'] },     // allowedHosts: Astro 5.4+
  // 구버전: vite: { server: { allowedHosts: ['.ts.net'] } },
})
```

## Angular (CLI 17+)
`angular.json` → `projects.<app>.architect.serve.options`:
```json
{ "host": "0.0.0.0", "allowedHosts": [".ts.net"] }
```
구버전(webpack dev server)도 같은 키. 스크립트 인자로는 `ng serve --host 0.0.0.0 --allowed-hosts .ts.net`.

## webpack-dev-server 직접 사용 / Vue CLI
`webpack.config.*`의 `devServer` 또는 `vue.config.js`의 `devServer`:
```js
devServer: { host: '0.0.0.0', allowedHosts: ['.ts.net', 'localhost'] }
```
- 배열에 `localhost`를 함께 둬야 로컬 접속이 유지된다. IP는 기본 허용.
- `client.webSocketURL`이 `localhost`로 고정돼 있으면 `'auto://0.0.0.0:0/ws'`로.

## Create React App (react-scripts)
설정 파일이 없으므로 `.env.development.local`(gitignore 대상)에:
```
HOST=0.0.0.0
```
- CRA는 `proxy` 설정이 없으면 호스트 검사를 하지 않는다. `package.json`에 `proxy`가 있어 "Invalid Host header"가 나면 `DANGEROUSLY_DISABLE_HOST_CHECK=true`도 넣되(검사 해제) 사용자에게 알린다.

## Expo / React Native web
`npx expo start --web --host lan` 또는 `--tunnel`. Metro에는 호스트 검사가 없다.

## Django
개발 설정(`settings/dev.py`, 또는 `if DEBUG:` 블록)에만:
```python
ALLOWED_HOSTS += ['.ts.net', '<TS_IP>']
# 다른 출처(예: :5173 프론트)에서 POST하는 경우만
CSRF_TRUSTED_ORIGINS += ['http://*.ts.net:5173']
```
실행: `python manage.py runserver 0.0.0.0:8000`. django-cors-headers를 쓰면 `CORS_ALLOWED_ORIGIN_REGEXES += [r'^https?://[^/]+\.ts\.net(:\d+)?$']`.

## Rails
`config/environments/development.rb`:
```ruby
config.hosts << ".ts.net"
```
IP는 개발 환경 기본 허용. 실행: `bin/rails s -b 0.0.0.0`(또는 `bin/dev`의 Procfile.dev에 `-b 0.0.0.0`). vite_ruby는 `config/vite.json`의 development에 `"host": "0.0.0.0"`.

## Laravel (+ Vite)
- `php artisan serve --host=0.0.0.0`
- 페이지가 Vite 자산을 `http://localhost:5173`으로 불러오면 휴대폰에서 깨진다 → `vite.config.js`:
```js
server: { host: '0.0.0.0', hmr: { host: '<Tailscale DNS>' }, cors: { origin: /\.ts\.net(:\d+)?$/ }, allowedHosts: ['.ts.net'] }
```
`hmr.host`는 기기 이름이라 저장소에 남기면 다른 사람에게 맞지 않는다 → `process.env.VITE_HMR_HOST`로 읽고 값은 `.env`(gitignore)에.

## Flask / FastAPI / Express / Go / Spring 등 (호스트 검사 없음)
바인딩만 확인한다: `flask run --host 0.0.0.0`, `uvicorn app:app --host 0.0.0.0`, Express `app.listen(port)`(호스트 인자 `'localhost'`/`'127.0.0.1'`이면 제거하거나 env로), Go `":8080"`(`"localhost:8080"`이면 변경), Spring `server.address` 미설정 확인. Express `host-validation`, Fastify `trustProxy` 등 별도 미들웨어가 있으면 `.ts.net`을 허용 목록에 추가. 프론트가 직접 부르면 CORS에 `*.ts.net` origin 정규식 허용(개발 전용).
