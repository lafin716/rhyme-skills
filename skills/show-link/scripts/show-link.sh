#!/usr/bin/env bash
# show-link: 파일(주로 스크린샷)을 갤러리 페이지로 묶어 0.0.0.0에 띄우고 localhost·LAN·Tailscale URL을 출력한다.
#   show-link.sh <이름> <파일|폴더>...   이름 = URL 경로(예: hosts-list)
#   show-link.sh --list                  띄운 갤러리 목록
#   show-link.sh --stop                  서버 종료
# 환경 변수: SHOW_LINK_PORT(기본 8765), SHOW_LINK_ROOT(기본 ${TMPDIR:-/tmp}/show-link)
# 필요: bash, python3, curl (macOS·Linux)
set -euo pipefail
BASE=${TMPDIR:-/tmp}
ROOT=${SHOW_LINK_ROOT:-${BASE%/}/show-link}
PORT=${SHOW_LINK_PORT:-8765}
PIDFILE=$ROOT/.server.pid
LOG=$ROOT/.server.log
mkdir -p "$ROOT"

running() { [[ -f $PIDFILE ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

case "${1:-}" in
  --stop)
    if running && kill "$(cat "$PIDFILE")" 2>/dev/null; then echo "stopped"; else echo "not running"; fi
    rm -f "$PIDFILE"
    exit 0 ;;
  --list)
    find "$ROOT" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
    running && echo "server: running on port $PORT (pid $(cat "$PIDFILE"))" || echo "server: not running"
    exit 0 ;;
  -h|--help|"")
    sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
    [[ -n "${1:-}" ]] && exit 0 || exit 1 ;;
esac
if [[ $# -lt 2 ]]; then echo "usage: show-link.sh <name> <file|dir>..." >&2; exit 1; fi
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

NAME=$(printf '%s' "$1" | tr -c 'A-Za-z0-9._-' '-' | sed 's/^[.-]*//'); shift
[[ -n $NAME ]] || { echo "invalid name" >&2; exit 1; }
DIR=$ROOT/$NAME
mkdir -p "$DIR"
for src in "$@"; do
  [[ -e $src ]] || { echo "not found: $src" >&2; exit 1; }
  if [[ -d $src ]]; then
    [[ "$(cd "$src" && pwd)" == "$(cd "$DIR" && pwd)" ]] || cp -R "$src"/. "$DIR"/
  else
    [[ "$(cd "$(dirname "$src")" && pwd)" == "$(cd "$DIR" && pwd)" ]] || cp "$src" "$DIR"/
  fi
done

# 갤러리: 이미지는 크게, 동영상은 플레이어, 나머지는 링크 (파일명은 HTML·URL 이스케이프)
python3 - "$DIR" "$NAME" <<'PY'
import html, os, sys, urllib.parse
d, name = sys.argv[1], sys.argv[2]
img = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.avif')
vid = ('.mp4', '.webm', '.mov')
out = ["<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
       f"<title>{html.escape(name)}</title>",
       "<style>body{font-family:-apple-system,system-ui,sans-serif;background:#f4f6fa;margin:0;padding:16px;color:#1b2333}"
       "h1{font-size:18px}figure{margin:0 0 24px;background:#fff;border-radius:12px;padding:12px;box-shadow:0 1px 3px #0002}"
       "img,video{max-width:100%;height:auto;display:block;margin:auto;border:1px solid #e3e7ef;border-radius:8px}"
       "figcaption{font-size:13px;color:#566;margin-top:8px;text-align:center}"
       "@media(prefers-color-scheme:dark){body{background:#111418;color:#e6e9ef}figure{background:#1b2028}figcaption{color:#9aa}}</style>",
       f"<h1>{html.escape(name)}</h1>"]
files = []
for root, dirs, fs in os.walk(d):
    dirs[:] = sorted(x for x in dirs if not x.startswith('.'))
    for f in fs:
        rel = os.path.relpath(os.path.join(root, f), d)
        if rel != 'index.html' and not f.startswith('.'):
            files.append(rel)
for rel in sorted(files):
    url, label = urllib.parse.quote(rel), html.escape(rel)
    low = rel.lower()
    if low.endswith(img):
        out.append(f"<figure><a href='{url}'><img src='{url}' loading=lazy alt='{label}'></a><figcaption>{label}</figcaption></figure>")
    elif low.endswith(vid):
        out.append(f"<figure><video src='{url}' controls preload=metadata></video><figcaption>{label}</figcaption></figure>")
    else:
        out.append(f"<p><a href='{url}'>{label}</a></p>")
if not files:
    out.append("<p>(no files)</p>")
with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out) + '\n')
print(' '.join(sorted(files)), file=open(os.path.join(d, '.files'), 'w'))
PY

# 서버: 떠 있으면 재사용, 포트가 다른 프로세스에 잡혀 있으면 실패
if ! running; then
  nohup python3 -m http.server "$PORT" --bind 0.0.0.0 --directory "$ROOT" > "$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    curl -sf -o /dev/null "http://127.0.0.1:$PORT/$NAME/" && break
    running || break
    sleep 0.3
  done
  if ! running; then
    rm -f "$PIDFILE"
    echo "server failed to start on port $PORT (in use? try SHOW_LINK_PORT=<port>):" >&2
    tail -3 "$LOG" >&2
    exit 1
  fi
fi
curl -sf -o /dev/null "http://127.0.0.1:$PORT/$NAME/" || { echo "server not responding (see $LOG)" >&2; exit 1; }

# 주소 수집 (macOS·Linux)
LAN=""
if command -v ipconfig >/dev/null 2>&1; then
  LAN=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
fi
if [[ -z $LAN ]] && command -v ip >/dev/null 2>&1; then
  LAN=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="src"){print $(i+1); exit}}' || true)
fi
if [[ -z $LAN ]] && command -v hostname >/dev/null 2>&1; then
  LAN=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
fi
TS=$(command -v tailscale 2>/dev/null || true)
[[ -z $TS && -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]] && TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
TSDNS="" TSIP=""
if [[ -n $TS ]]; then
  TSDNS=$("$TS" status --self --json 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))" 2>/dev/null || true)
  TSIP=$("$TS" ip -4 2>/dev/null | head -1 || true)
fi

echo "localhost: http://localhost:$PORT/$NAME/"
if [[ -n $LAN ]]; then echo "LAN:       http://$LAN:$PORT/$NAME/"; fi
if [[ -n $TSDNS ]]; then echo "Tailscale: http://$TSDNS:$PORT/$NAME/"; fi
if [[ -n $TSIP ]]; then echo "Tailscale: http://$TSIP:$PORT/$NAME/"; fi
echo "files:     $(cat "$DIR/.files")"
rm -f "$DIR/.files"
