import asyncio
from http import HTTPStatus
import os
import websockets

SERVER_SOCKET = None


async def process_request(path, request_headers):
    # إذا فتحت الرابط من المتصفح كـ HTTP عادي، اعرض index.html
    if request_headers.get("Upgrade", "").lower() != "websocket":
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                body = f.read().encode("utf-8")
            return (
                HTTPStatus.OK,
                [("Content-Type", "text/html; charset=utf-8")],
                body,
            )
        except Exception:
            return (
                HTTPStatus.NOT_FOUND,
                [("Content-Type", "text/plain")],
                b"index.html not found",
            )
    return None  # استكمال الاتصال كـ WebSocket


async def handler(websocket, path=None):
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
