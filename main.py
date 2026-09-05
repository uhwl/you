import asyncio
import os
import websockets

SERVER_SOCKET = None

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
    except Exception:
        pass

async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
