#!/bin/bash
# bio 服务器入口 - 停止所有服务（tmux 会话保留）
pkill -f "$HOME/services/bin/ttyd" 2>/dev/null && echo "ttyd: 已停止"
pkill -f "$HOME/services/dashboard.py" 2>/dev/null && echo "dashboard: 已停止"
pkill -f "$HOME/services/code-server" 2>/dev/null && echo "code-server: 已停止"
pkill -f "$HOME/services/csproxy.py" 2>/dev/null && echo "csproxy: 已停止"
sleep 0.5
echo "剩余 tmux 会话（未受影响）:"; tmux ls 2>/dev/null || echo "  (无)"
