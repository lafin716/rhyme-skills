#!/usr/bin/env bash
# show-dev: 개발 서버를 Tailscale로 외부(내 tailnet 기기)에서 열기 위한 보조 스크립트.
#   show-dev.sh check [--refresh]       Tailscale 실행 여부 확인(성공 결과는 하루 동안 캐시). 실패 시 exit 2
#   show-dev.sh urls <port> [path]      localhost·LAN·Tailscale 접속 URL 출력
#   show-dev.sh verify <port> [path]    localhost와 Tailscale 도메인(Host 헤더)으로 요청해 허용 호스트 오류 검사
# 환경 변수: SHOW_DEV_CACHE(기본 ${XDG_CACHE_HOME:-~/.cache}/show-dev/tailscale.env), SHOW_DEV_TAILSCALE(tailscale 실행 파일 경로)
# 필요: bash, curl, python3 (macOS·Linux)
set -euo pipefail
CACHE=${SHOW_DEV_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/show-dev/tailscale.env}
TODAY=$(date +%F)

find_ts() {
  local ts
  ts=${SHOW_DEV_TAILSCALE:-$(command -v tailscale 2>/dev/null || true)}
  [[ -z $ts && -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]] && ts=/Applications/Tailscale.app/Contents/MacOS/Tailscale
  printf '%s' "$ts"
}

# 실제 확인 → TS_STATE/TS_DNS/TS_IP 설정. 성공일 때만 캐시에 쓴다(실패는 매번 다시 확인해 사용자가 켜면 바로 반영).
probe() {
  local ts json
  TS_STATE="" TS_DNS="" TS_IP="" TS_REASON=""
  ts=$(find_ts)
  if [[ -z $ts || ! -x $ts ]]; then TS_STATE=missing; TS_REASON="tailscale CLI/app not found"; return; fi
  json=$("$ts" status --self --peers=false --json 2>/dev/null || true)
  if [[ -z $json ]]; then TS_STATE=stopped; TS_REASON="tailscale daemon not responding"; return; fi
  eval "$(printf '%s' "$json" | python3 -c '
import json, shlex, sys
d = json.load(sys.stdin)
s = d.get("Self") or {}
ips = [i for i in (s.get("TailscaleIPs") or []) if ":" not in i]
print("TS_BACKEND=%s" % shlex.quote(d.get("BackendState", "")))
print("TS_DNS=%s" % shlex.quote((s.get("DNSName") or "").rstrip(".")))
print("TS_IP=%s" % shlex.quote(ips[0] if ips else ""))
print("TS_ONLINE=%s" % ("1" if s.get("Online", True) else "0"))
' 2>/dev/null || echo 'TS_BACKEND=unknown')"
  if [[ ${TS_BACKEND:-} != Running ]]; then TS_STATE=stopped; TS_REASON="backend state: ${TS_BACKEND:-unknown}"; return; fi
  if [[ -z $TS_IP ]]; then TS_STATE=stopped; TS_REASON="no tailscale IPv4 address"; return; fi
  TS_STATE=ok
  [[ -z $TS_DNS ]] && TS_REASON="MagicDNS name unavailable (use IP)"
  mkdir -p "$(dirname "$CACHE")"
  printf 'DATE=%s\nTS_STATE=ok\nTS_DNS=%s\nTS_IP=%s\n' "$TODAY" "$TS_DNS" "$TS_IP" > "$CACHE"
}

load() {  # 오늘 날짜의 성공 캐시가 있으면 사용, 아니면 probe
  if [[ ${1:-} != --refresh && -f $CACHE ]] && grep -qx "DATE=$TODAY" "$CACHE"; then
    TS_STATE=$(sed -n 's/^TS_STATE=//p' "$CACHE"); TS_DNS=$(sed -n 's/^TS_DNS=//p' "$CACHE"); TS_IP=$(sed -n 's/^TS_IP=//p' "$CACHE")
    TS_REASON="" CACHED=1
  else
    CACHED=0; probe
  fi
}

lan_ip() {
  local ip=""
  command -v ipconfig >/dev/null 2>&1 && ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
  [[ -z $ip ]] && command -v ip >/dev/null 2>&1 && ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="src"){print $(i+1); exit}}' || true)
  [[ -z $ip ]] && ip=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
  printf '%s' "$ip"
}

require_ok() {
  load "${1:-}"
  if [[ $TS_STATE != ok ]]; then
    echo "tailscale: $TS_STATE ($TS_REASON)" >&2
    exit 2
  fi
}

cmd=${1:-}; shift || true
case "$cmd" in
  check)
    load "${1:-}"
    if [[ $TS_STATE == ok ]]; then
      echo "tailscale: ok$([[ $CACHED == 1 ]] && echo " (cached $TODAY)")"
      echo "dns: ${TS_DNS:-<none>}"
      echo "ip: $TS_IP"
      [[ -n $TS_REASON ]] && echo "note: $TS_REASON"
      exit 0
    fi
    echo "tailscale: $TS_STATE ($TS_REASON)"
    exit 2 ;;
  urls)
    port=${1:?usage: show-dev.sh urls <port> [path]}; path=${2:-/}
    require_ok
    lan=$(lan_ip)
    echo "localhost: http://localhost:$port$path"
    [[ -n $lan ]] && echo "LAN:       http://$lan:$port$path"
    [[ -n $TS_DNS ]] && echo "Tailscale: http://$TS_DNS:$port$path"
    echo "Tailscale: http://$TS_IP:$port$path" ;;
  verify)
    port=${1:?usage: show-dev.sh verify <port> [path]}; path=${2:-/}
    require_ok
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
    if [[ -n $TS_DNS ]]; then
      # MagicDNS가 이 기기에서 안 풀려도 Host 헤더 검사가 되도록 Tailscale IP로 고정 해석
      check_one "tailscale-dns ($TS_DNS)" "$TS_DNS" --resolve "$TS_DNS:$port:$TS_IP"
    fi
    check_one "tailscale-ip ($TS_IP)" "$TS_IP"
    exit $fail ;;
  -h|--help|"")
    sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
    [[ -n $cmd ]] && exit 0 || exit 1 ;;
  *) echo "unknown command: $cmd" >&2; exit 1 ;;
esac
