import uuid
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGA_PART_1 = "MDE5ZTIwOWQtNmI1NC03YzlmLWJhZDQ" + "tMTUxMzA3YWY1MDYz"
GIGA_PART_2 = "OjdlZjE4NGY1LThkMGQtNGNmNS1iNjJlLWVhM2NiZWQyNzcxNQ=="
AUTH_KEY = f"{GIGA_PART_1}{GIGA_PART_2}"

token_cache = {"token": "", "expires_at": 0}
chat_histories = {}


def get_token() -> str:
    now = time.time()
    if token_cache["token"] and now < token_cache["expires_at"] - 60:
        return token_cache["token"]
    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {AUTH_KEY}"
            },
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False,
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            token_cache["token"] = data.get("access_token", "")
            token_cache["expires_at"] = (data.get("expires_at", 0) / 1000.0) or (now + 1700)
            return token_cache["token"]
        print(f"[GIGACHAT-AUTH] HTTP {res.status_code}: {res.text[:150]}")
    except Exception as e:
        print(f"[GIGACHAT-AUTH] Сбой: {e}")
    return ""


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])
    token = get_token()
    if not token:
        return "⚠️ Не удалось подключиться к GigaChat. Проверьте ключ в giga_ai.py."

    prompt = (
        f"Ты — профессиональный, бережный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Отбой пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Отвечай строго на русском языке, тепло, глубоко и по делу (2–4 предложения), учитывая прошлые сообщения."
    )
    messages = [{"role": "system", "content": prompt}] + chat_histories[user_id][-6:] + [{"role": "user", "content": user_text}]

    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"model": "GigaChat", "messages": messages, "temperature": 0.7, "max_tokens": 350},
            verify=False,
            timeout=12
        )
        if res.status_code == 200:
            reply = res.json()["choices"].pop(0)["message"]["content"].strip()
            if reply:
                chat_histories[user_id].extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": reply}
                ])
                return reply
        print(f"[GIGACHAT-CHAT] HTTP {res.status_code}: {res.text[:150]}")
    except Exception as e:
        print(f"[GIGACHAT-CHAT] Сбой: {e}")

    return "🌙 Я рядом и слушаю тебя. Расскажи подробнее, что мешает тебе расслабиться перед сном?"
