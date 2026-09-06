import asyncio
import os
import websockets
from websockets.http import Headers

SERVER_SOCKET = None


async def process_request(path, request_headers):
    # إذا كان الطلب فتح صفحة ويب عادية (HTTP) وليس WebSocket
    if request_headers.get("Upgrade", "").lower() != "websocket":
        try:
            with open("index.html", "rb") as f:
                body = f.read()
            headers = Headers([("Content-Type", "text/html; charset=utf-8")])
            # إرجاع الاستجابة بالصيغة الصحيحة للمكتبة (Status Code, Headers, Body)
            return (200, headers, body)
        except Exception:
            headers = Headers([("Content-Type", "text/plain")])
            return (404, headers, b"index.html not found")

    # السماح باستكمال اتصال WebSocket
    return None


async def handler(websocket):
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
    port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(
        handler, "0.0.0.0", port, process_request=process_request
    ):
        print(f"[*] Server running on port {port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
