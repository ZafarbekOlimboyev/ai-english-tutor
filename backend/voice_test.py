"""Ovoz endpointlari sinovи — /tts, /stt, /session/{id}/voice (round-trip)."""
import json
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:9003"


def call(path, body=None, method="POST", token=None, raw=False):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return (r.status, r.read()) if raw else (r.status, json.load(r))
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]


def upload_audio(path, wav_bytes, token, field="file"):
    """multipart/form-data bilan audio yuborish."""
    boundary = "----b" + uuid.uuid4().hex
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="{field}"; filename="a.wav"\r\n'.encode()
    body += b"Content-Type: audio/wav\r\n\r\n"
    body += wav_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


# Register
_, r = call("/auth/register", {"device_id": "voicedev", "name": "V"})
t = r["token"]
print("register OK")

# 1) TTS
print("\n=== /tts ===")
code, wav = call("/tts", {"text": "Hello Jasur, tell me about your day."}, token=t, raw=True)
print("status:", code, "| WAV bayt:", len(wav) if code == 200 else wav)

if code == 200:
    # 2) STT — TTS chiqargan audioni qaytarib beramiz
    print("\n=== /stt (TTS audioни transkripsiya) ===")
    code, res = upload_audio("/stt", wav, t)
    print("status:", code, "| matn:", res.get("text") if isinstance(res, dict) else res)

    # 3) /session/{id}/voice — to'liq ovozli navbat
    print("\n=== /session/{id}/voice ===")
    _, s = call("/session/start", {"scenario_id": "daily_checkin"}, token=t)
    sid = s["session_id"]
    print("start OK, AI:", s["ai_opening"][:40])
    code, res = upload_audio(f"/session/{sid}/voice", wav, t)
    if isinstance(res, dict):
        print("status:", code)
        print("  user_text (STT):", res.get("user_text"))
        print("  AI reply:", (res.get("reply") or "")[:60])
        print("  reply_audio_b64:", len(res.get("reply_audio_b64", "")), "belgi (base64 WAV)")
        print("  turn:", res.get("turn_count"))
    else:
        print("status:", code, res)

print("\n=== OVOZ TEST TUGADI ===")
