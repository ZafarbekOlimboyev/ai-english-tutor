"""To'liq MVP oqimi + xavfsizlik tuzatishlari sinovи (v0.4.0)."""
import json
import threading
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:9003"


def call(path, body=None, method="POST", token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, {}
    except Exception as e:
        return f"ERR:{type(e).__name__}", {}


def new_user(device="d", name="Test"):
    _, r = call("/auth/register", {"device_id": device, "name": name, "goal": "work"})
    return r["token"]


print("=== 0) AUTHSIZ -> 401 ===")
code, _ = call("/session/start", {"scenario_id": "free_talk"})
print("  ->", code, "(401 kutildi)")

print("\n=== 1) REGISTER YANGI TOKEN (device_id bilan token o'g'irlanmaydi) ===")
_, a = call("/auth/register", {"device_id": "same-device", "name": "A"})
_, b = call("/auth/register", {"device_id": "same-device", "name": "B"})
print("  2 ta register (bir xil device_id) -> tokenlar farqli:", a["token"] != b["token"])
print("  user_id lar farqli:", a["user_id"] != b["user_id"], "(hisob o'g'irlash yopildi)")

t = new_user("main-device")

print("\n=== 2) INPUT VALIDATSIYA ===")
code, _ = call(f"/session/start", {"scenario_id": "free_talk"}, token=t)
sid_tmp = _.get("session_id") if isinstance(_, dict) else None
code, _ = call(f"/session/{sid_tmp}/message", {"message": ""}, token=t)
print("  bo'sh message ->", code, "(422 kutildi)")
code, _ = call("/assess", {"samples": []}, token=t)
print("  bo'sh samples ->", code, "(422 kutildi)")

print("\n=== 3) DARAJA ANIQLASH (LLM budjetига kiradi) ===")
code, lvl = call("/assess", {"samples": [
    "I am work as programmer for two year.",
    "Yesterday I go to shop and buy some food.",
]}, token=t)
print("  status", code, "| daraja:", lvl.get("level"))

print("\n=== 4) SUHBAT + FEEDBACK (2-sessiya endi limit tugagan, yangi user olamiz) ===")
t2 = new_user("conv-device")
code, s = call("/session/start", {"scenario_id": "job_interview", "level": "B1"}, token=t2)
sid = s["session_id"]
print("  start:", code, "| AI:", s["ai_opening"][:40])
for msg in ["Hello, my name is Jasur. I am programmer.",
            "I want to join your company."]:
    code, r = call(f"/session/{sid}/message", {"message": msg}, token=t2)
    print(f"    turn {r.get('turn_count')}: {r.get('reply','')[:45]}")
code, fb = call(f"/session/{sid}/feedback", token=t2)
print("  feedback:", code, "| ball:", fb.get("fluency_score"))

print("\n=== 5) KUNLIK SESSIYA LIMITI (2-suhbat -> 402) ===")
code, r = call("/session/start", {"scenario_id": "restaurant"}, token=t2)
print("  2-start ->", code, "(402 kutildi)")

print("\n=== 6) TOCTOU KONKURENTLIK TESTI (8 parallel start, faqat 1 o'tishi kerak) ===")
t3 = new_user("race-device")
results = []
lock = threading.Lock()

def fire():
    c, _ = call("/session/start", {"scenario_id": "free_talk"}, token=t3)
    with lock:
        results.append(c)

threads = [threading.Thread(target=fire) for _ in range(8)]
for th in threads:
    th.start()
for th in threads:
    th.join()
ok = results.count(200)
paywall = results.count(402)
print(f"  natija ({len(results)} ta javob): {ok} ta 200, {paywall} ta 402, boshqa: {[r for r in results if r not in (200, 402)]}")
print("  -> TOCTOU " + ("TUZATILDI" if ok == 1 else f"MUAMMO! {ok} ta ruxsat berildi"))

print("\n=== 7) /auth/me ===")
code, m = call("/auth/me", method="GET", token=t2)
print(f"  sessiya: {m['sessions_today']}/{m['daily_limit']} | LLM: {m['llm_calls_today']}/{m['daily_llm_limit']}")

print("\n=== TEST TUGADI ===")
