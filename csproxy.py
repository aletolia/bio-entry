#!/usr/bin/env python3
# csproxy.py — 为 code-server 注入 X-Forwarded-* 头（修复 WebVPN 链路下 WS Origin 检查 403）
# 监听 127.0.0.1:8081 -> 转发 127.0.0.1:8080（HTTP 与 WebSocket 均透传）
import asyncio

LISTEN = ("127.0.0.1", 8081)
TARGET = ("127.0.0.1", 8080)
EXTRA = b"X-Forwarded-Host: webvpn.wmu.edu.cn\r\nX-Forwarded-Proto: https\r\n"

async def pipe(r, w):
    try:
        while True:
            data = await r.read(65536)
            if not data:
                break
            w.write(data)
            await w.drain()
    except Exception:
        pass
    finally:
        try:
            w.close()
        except Exception:
            pass

async def handle(cr, cw):
    try:
        tr, tw = await asyncio.open_connection(*TARGET)
    except Exception:
        try:
            cw.close()
        except Exception:
            pass
        return
    buf = b""
    try:
        while b"\r\n\r\n" not in buf and len(buf) < 262144:
            chunk = await asyncio.wait_for(cr.read(4096), timeout=30)
            if not chunk:
                break
            buf += chunk
    except Exception:
        pass
    if buf:
        low = buf.lower()
        if b"upgrade: websocket" in low and b"x-forwarded-host" not in low:
            head, sep, rest = buf.partition(b"\r\n\r\n")
            buf = head + b"\r\n" + EXTRA + b"\r\n" + rest
        try:
            tw.write(buf)
            await tw.drain()
        except Exception:
            pass
    await asyncio.gather(pipe(cr, tw), pipe(tr, cw))

async def main():
    server = await asyncio.start_server(handle, *LISTEN)
    print("csproxy %s:%d -> %s:%d" % (LISTEN[0], LISTEN[1], TARGET[0], TARGET[1]), flush=True)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
