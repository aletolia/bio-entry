#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# bio 服务器仪表盘：入口链接 / tmux 会话 / GPU / 系统状态（仅标准库）
import base64, html, os, socket, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = os.path.expanduser("~")
ENV = {}
try:
    for _line in open(os.path.join(HOME, "services", "env")):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            ENV[_k.strip()] = _v.strip()
except Exception:
    pass
DASH_USER = ENV.get("DASH_USER", "bio")
DASH_PASS = ENV.get("DASH_PASS", "")

def sh(cmd, timeout=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip()
    except Exception:
        return ""

def port_open(port):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
        s.close(); return True
    except Exception:
        return False

def tmux_rows():
    out = sh("tmux ls -F '#{session_name}\t#{session_windows}\t#{?session_attached,已连接,未连接}\t#{t:session_created}'")
    return [ln.split("\t") for ln in out.splitlines() if ln.count("\t") >= 3]

def gpu_rows():
    out = sh("nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits")
    return [[p.strip() for p in ln.split(",")] for ln in out.splitlines()]

def entry_links():
    rows = []
    try:
        for ln in open(os.path.join(HOME, ".rstudio-entry", "urls.txt")):
            ln = ln.strip()
            if ln and "  " in ln:
                name, url = ln.split(None, 1)
                rows.append((name, url.strip()))
    except Exception:
        pass
    return rows

def sysinfo():
    info = []
    try:
        info.append(("运行时间", sh("uptime -p") or "?"))
        la = os.getloadavg()
        info.append(("负载", "%.2f / %.2f / %.2f" % la))
    except Exception:
        pass
    try:
        mem = {}
        for ln in open("/proc/meminfo"):
            k, v = ln.split(":", 1)
            mem[k] = int(v.strip().split()[0])
        info.append(("内存", "%.0f GB 可用 / %.0f GB" % (mem.get("MemAvailable", 0) / 1048576.0, mem.get("MemTotal", 0) / 1048576.0)))
    except Exception:
        pass
    try:
        st = os.statvfs(HOME)
        info.append(("家目录", "%.0f GB 可用 / %.0f GB" % (st.f_bavail * st.f_frsize / 1e9, st.f_blocks * st.f_frsize / 1e9)))
    except Exception:
        pass
    d = sh("df -h /home/data 2>/dev/null | tail -1 | awk '{print $4\" 可用 / \"$2}'")
    if d:
        info.append(("数据盘", d))
    return info

def esc(s):
    return html.escape(str(s))

def render():
    svc = [("终端 ttyd+tmux", 7681), ("仪表盘", 8899), ("VS Code", 8080), ("RStudio", 8787)]
    svc_html = "".join(
        '<span class="pill %s">%s %s:%d</span>' % ("on" if port_open(p) else "off", "●", esc(n), p)
        for n, p in svc)
    links = entry_links()
    links_html = "".join(
        '<li><a href="%s" target="_blank">%s</a></li>' % (esc(u), esc(n)) for n, u in links
    ) or '<li class="dim">（暂无 — 在 RStudio 里执行 source("~/services/entry.R") 生成）</li>'
    tm = tmux_rows()
    tm_html = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c), esc(d))
        for a, b, c, d in tm) or '<tr><td colspan="4" class="dim">（没有 tmux 会话）</td></tr>'
    gm = gpu_rows()
    gpu_html = "".join(
        "<tr><td>%s</td><td>%s%%</td><td>%s / %s MB</td><td>%s°C</td></tr>" % (esc(a), esc(b), esc(c), esc(d), esc(e))
        for a, b, c, d, e in gm) or '<tr><td colspan="4" class="dim">（无 GPU 信息）</td></tr>'
    sys_html = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v)) for k, v in sysinfo())
    return """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="15"><title>bio 服务器入口</title>
<style>
body{background:#0f1216;color:#d7dde3;font:14px/1.6 system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;padding:24px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;color:#8ea9ff;margin:22px 0 8px}
a{color:#7ec8ff;text-decoration:none}a:hover{text-decoration:underline}
.pill{display:inline-block;background:#1a2027;border-radius:12px;padding:3px 10px;margin:0 8px 6px 0;font-size:13px}
.pill .on{color:#7dffa1}.pill.on{color:#7dffa1}.pill.off{color:#8b98a5}
table{border-collapse:collapse;width:100%;max-width:760px}td,th{border-bottom:1px solid #232b34;padding:6px 10px;text-align:left;font-size:13px}
th{color:#8b98a5;font-weight:500}.dim{color:#66707a}
.footer{color:#54606c;font-size:12px;margin-top:26px}
ul{padding-left:18px;margin:6px 0}
</style></head><body>
<h1>bio 服务器入口</h1>
<div>__SVC__</div>
<h2>入口链接（需先登录 WebVPN）</h2><ul>__LINKS__</ul>
<h2>tmux 会话</h2><table><tr><th>会话</th><th>窗口数</th><th>状态</th><th>创建时间</th></tr>__TMUX__</table>
<h2>GPU</h2><table><tr><th>型号</th><th>利用率</th><th>显存</th><th>温度</th></tr>__GPU__</table>
<h2>系统</h2><table>__SYS__</table>
<div class="footer">自动刷新 15s · bio@bio-Super-Server · 由 ~/services/dashboard.py 提供</div>
</body></html>""".replace("__SVC__", svc_html).replace("__LINKS__", links_html).replace("__TMUX__", tm_html).replace("__GPU__", gpu_html).replace("__SYS__", sys_html)

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass
    def _auth(self):
        h = self.headers.get("Authorization", "")
        if h.startswith("Basic "):
            try:
                u, _, p = base64.b64decode(h[6:]).decode("utf-8", "ignore").partition(":")
                if u == DASH_USER and p == DASH_PASS:
                    return True
            except Exception:
                pass
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="bio"')
        self.end_headers()
        return False
    def do_GET(self):
        if not self._auth():
            return
        data = render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8899), H).serve_forever()
