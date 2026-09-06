import os
from aiohttp import web

SERVER_SOCKET = None


async def handle_root(request):
    global SERVER_SOCKET

    # إذا كان الطلب اتصال WebSocket (سواء من T440p أو المتصفح)
    if request.headers.get("Upgrade", "").lower() == "websocket":
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = msg.data
                    if data == "REGISTER_T440P":
                        SERVER_SOCKET = ws
                        print("[+] T440p Connected!")
                    elif data.startswith("PUNCH:"):
                        client_ip = data.split(":")[1]
                        if SERVER_SOCKET:
                            await SERVER_SOCKET.send_str(f"{client_ip},19132")
                            await ws.send_str("PUNCH_SENT")
                            print(f"[+] Hole punch requested for {client_ip}")
        except Exception as e:
            print(f"[-] Connection closed: {e}")

        return ws

    # إذا كان طلب HTTP عادي، يتم عرض الواجهة index.html
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except Exception:
        return web.Response(text="index.html not found", status=404)


app = web.Application()
app.router.add_route("*", "/{tail:.*}", handle_root)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
