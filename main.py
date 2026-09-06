import asyncio
import os
import websockets

SERVER_SOCKET = None


async def process_request(*args, **kwargs):
    # استخراج الهيدر بنجاح مع جميع إصدارات websockets القديمة والحديثة
    req = args[1] if len(args) > 1 else args[0]
    headers = getattr(req, "headers", req)

    upgrade_header = ""
    if hasattr(headers, "get"):
        upgrade_header = headers.get("Upgrade", "")

    # إذا كان الطلب فتح صفحة عادي وليس WebSocket
    if upgrade_header.lower() != "websocket":
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                html_code = f.read()
            return (
                200,
                [("Content-Type", "text/html; charset=utf-8")],
                html_code.encode("utf-8"),
            )
        except Exception:
            return (404, [("Content-Type", "text/plain")], b"index.html not found")

    return None  # السماح بمرور اتصال الـ WebSocket


async def handler(websocket, *args):
    global SERVER_SOCKET
    try:
        async for message in websocket:
            if message == "REGISTER_T440P":
                SERVER_SOCKET = websocket
                print("[+] T440p Connected!")
            elif message.startswith("PUNCH:"):
                client_ip = message.split(":")[1]
                if SERVER_SOCKET:
                    await SERVER_SOCKET.send(f"{client_ip},19132")
                    await websocket.send("PUNCH_SENT")
                    print(f"[+] Hole punch requested for {client_ip}")
    except Exception:
        pass


async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(
        handler, "0.0.0.0", port, process_request=process_request
    ):
        print(f"[*] Server running on port {port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
