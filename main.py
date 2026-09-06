import os
import time
import ipaddress
from aiohttp import web

SERVER_SOCKET = None
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "acore_secret_pass_123")

# تتبع وقت آخر طلب PUNCH لكل IP لمنع الإغراق
LAST_PUNCH_TIMES = {}

async def handle_root(request):
    global SERVER_SOCKET, LAST_PUNCH_TIMES

    # إذا كان الاتصال WebSocket
    if request.headers.get("Upgrade", "").lower() == "websocket":
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # جلب IP العميل الحقيقي (مع مراعاة البروكسي الخاص بـ Render)
        client_real_ip = request.headers.get("X-Forwarded-For", request.remote).split(',')[0].strip()

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = msg.data.strip()

                    # 1. الحفاظ على الاتصال نشطاً لمنع النوم
                    if data == "PING":
                        await ws.send_str("PONG")
                        continue

                    # 2. تسجيل T440p بالمفتاح السري حصراً
                    if data == f"REGISTER_T440P:{SECRET_TOKEN}":
                        SERVER_SOCKET = ws
                        await ws.send_str("REGISTERED_OK")
                        print(f"[+] T440p Registered Successfully from {client_real_ip}")

                    # 3. طلب الثقب (PUNCH) مع حماية Rate Limit وفحص IP
                    elif data.startswith("PUNCH:"):
                        now = time.time()
                        last_time = LAST_PUNCH_TIMES.get(client_real_ip, 0)

                        # حظر الطلبات المكررة خلال أقل من 5 ثوانٍ
                        if now - last_time < 5:
                            await ws.send_str("ERROR: RATE_LIMIT_EXCEEDED")
                            continue

                        target_ip = data.split(":", 1)[1].strip()

                        # التحقق من أن الـ IP المرسل هو عنوان IPv6 أو IPv4 صالح
                        try:
                            ipaddress.ip_address(target_ip)
                        except ValueError:
                            await ws.send_str("ERROR: INVALID_IP")
                            continue

                        # توجيه الطلب لـ T440p إذا كان متصلاً
                        if SERVER_SOCKET and not SERVER_SOCKET.closed:
                            LAST_PUNCH_TIMES[client_real_ip] = now
                            await SERVER_SOCKET.send_str(f"{target_ip},19132")
                            await ws.send_str("PUNCH_SENT")
                            print(f"[+] Hole punch requested for {target_ip} by {client_real_ip}")
                        else:
                            await ws.send_str("ERROR: SERVER_NOT_CONNECTED")

        except Exception as e:
            print(f"[-] Connection error ({client_real_ip}): {e}")

        finally:
            # تنظيف المقبس تلقائياً عند انقطاع T440p
            if ws == SERVER_SOCKET:
                SERVER_SOCKET = None
                print("[-] T440p Disconnected!")

        return ws

    # إذا كان طلب HTTP عادي (عرض الصفحة)
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
