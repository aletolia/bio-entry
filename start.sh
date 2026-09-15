#!/bin/bash
# bio 服务器入口 - 一键启动（幂等）
SVC="$HOME/services"
[ -f "$SVC/env" ] && set -a && . "$SVC/env" && set +a
mkdir -p "$SVC/logs"

# 简单锁，防并发
LOCK=/tmp/.bio-services.lock
mkdir "$LOCK" 2>/dev/null || { echo "another start in progress"; exit 0; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

have() { ss -tln 2>/dev/null | grep -q ":$1 "; }

if have 7681; then echo "ttyd: 已在运行"; else
  (setsid nohup "$SVC/bin/ttyd" -p 7681 -i 127.0.0.1 -c "${TTYD_USER:-bio}:${TTYD_PASS}" -t fontSize=15 tmux new -A -s main > "$SVC/logs/ttyd.log" 2>&1 < /dev/null &)
  echo "ttyd: 已启动"
fi

if have 8899; then echo "dashboard: 已在运行"; else
  (setsid nohup python3 "$SVC/dashboard.py" > "$SVC/logs/dashboard.log" 2>&1 < /dev/null &)
  echo "dashboard: 已启动"
fi

if have 8080; then echo "code-server: 已在运行"; else
  if [ -x "$SVC/code-server/bin/code-server" ]; then
    (setsid nohup env PASSWORD="${CODE_PASS}" "$SVC/code-server/bin/code-server" --bind-addr 127.0.0.1:8080 --auth password --disable-telemetry --disable-update-check > "$SVC/logs/code-server.log" 2>&1 < /dev/null &)
    echo "code-server: 已启动"
  else
    echo "code-server: 未安装"
  fi
fi
sleep 1
ss -tln | grep -E ":7681 |:8899 |:8080 " || true
