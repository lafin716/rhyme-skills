#!/usr/bin/env bash
# show-dev: 0.0.0.0에 띄운 개발 서버의 외부 접속 주소를 출력하고 허용 호스트 오류를 검사하는 보조 스크립트.
#   show-dev.sh urls <port> [path]      localhost·LAN·Tailscale(있으면) 접속 URL 출력
#   show-dev.sh verify <port> [path]    localhost·LAN·Tailscale 도메인(Host 헤더)으로 요청해 허용 호스트 오류 검사
# Tailscale은 선택 사항이다 — 없거나 꺼져 있으면 해당 주소만 생략한다.
# 환경 변수: SHOW_DEV_TAILSCALE(tailscale 실행 파일 경로)
# 필요: bash, curl, python3 (macOS·Linux)
set -euo pipefail

# Tailscale 주소 수집(best-effort) → TS_DNS/TS_IP. 실패해도 빈 값으로 계속한다.
ts_addrs() {
  local ts json
  TS_DNS="" TS_IP=""
  ts=${SHOW_DEV_TAILSCALE:-$(command -v tailscale 2>/dev/null || true)}
  [[ -z $ts && -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]] && ts=/Applications/Tailscale.app/Contents/MacOS/Tailscale
  [[ -n $ts && -x $ts ]] || return 0
  json=$("$ts" status --self --peers=false --json 2>/dev/null || true)
  [[ -n $json ]] || return 0
  eval "$(printf '%s' "$json" | python3 -c '
import json, shlex, sys
d = json.load(sys.stdin)
if d.get("BackendState") != "Running":
    sys.exit()
s = d.get("Self") or {}
ips = [i for i in (s.get("TailscaleIPs") or []) if ":" not in i]
print("TS_DNS=%s" % shlex.quote((s.get("DNSName") or "").rstrip(".")))
print("TS_IP=%s" % shlex.quote(ips[0] if ips else ""))
' 2>/dev/null || true)"
  [[ -n $TS_IP ]] || TS_DNS=""
}

lan_ip() {
  local ip=""
  command -v ipconfig >/dev/null 2>&1 && ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
  [[ -z $ip ]] && command -v ip >/dev/null 2>&1 && ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="src"){print $(i+1); exit}}' || true)
  [[ -z $ip ]] && ip=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
  printf '%s' "$ip"
}

cmd=${1:-}; shift || true
case "$cmd" in
  urls)
    port=${1:?usage: show-dev.sh urls <port> [path]}; path=${2:-/}
    ts_addrs; lan=$(lan_ip)
    echo "localhost: http://localhost:$port$path"
    [[ -n $lan ]] && echo "LAN:       http://$lan:$port$path"
    [[ -n $TS_DNS ]] && echo "Tailscale: http://$TS_DNS:$port$path"
    [[ -n $TS_IP ]] && echo "Tailscale: http://$TS_IP:$port$path"
    [[ -z $TS_IP ]] && echo "Tailscale: (not running — skipped)"
    exit 0 ;;
  verify)
    port=${1:?usage: show-dev.sh verify <port> [path]}; path=${2:-/}
    ts_addrs; lan=$(lan_ip)
    fail=0
    check_one() {  # label host extra-curl-args...
      local label=$1 host=$2; shift 2
      local body code
      body=$(mktemp)
      code=$(curl -s -o "$body" -w '%{http_code}' --max-time 15 "$@" "http://$host:$port$path" || echo 000)
      if grep -qiE 'Blocked request|Invalid Host header|DisallowedHost|Invalid HTTP_HOST|Blocked hosts?:|is not allowed|allowedHosts|allowedDevOrigins' "$body"; then
        echo "$label: BLOCKED (http $code) — $(grep -oiE 'Blocked request[^<]{0,120}|Invalid Host header|Invalid HTTP_HOST header[^<]{0,80}|Blocked hosts?:[^<]{0,80}' "$body" | head -1)"
        fail=1
      elif [[ $code == 000 ]]; then
        echo "$label: NO RESPONSE (not listening on 0.0.0.0:$port?)"; fail=1
      elif [[ $code =~ ^[45] ]]; then
        echo "$label: http $code (check server log)"; fail=1
      else
        echo "$label: ok (http $code)"
      fi
      rm -f "$body"
    }
    check_one localhost 127.0.0.1
    [[ -n $lan ]] && check_one "lan ($lan)" "$lan"
    if [[ -n $TS_DNS ]]; then
      # MagicDNS가 이 기기에서 안 풀려도 Host 헤더 검사가 되도록 Tailscale IP로 고정 해석
      check_one "tailscale-dns ($TS_DNS)" "$TS_DNS" --resolve "$TS_DNS:$port:$TS_IP"
    fi
    [[ -n $TS_IP ]] && check_one "tailscale-ip ($TS_IP)" "$TS_IP"
    exit $fail ;;
  -h|--help|"")
    sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
    [[ -n $cmd ]] && exit 0 || exit 1 ;;
  *) echo "unknown command: $cmd" >&2; exit 1 ;;
esac
