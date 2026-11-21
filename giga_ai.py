import uuid
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGA_PART_1 = "MDE5ZTIwOWQtNmI1NC03YzlmLWJhZDQ" + "tMTUxMzA3YWY1MDYz"
GIGA_PART_2 = "OmQzNDlmOTE1LTAyOTItNDUzMi05ZmM5LWJjYTgzNTQ5MjViMg=="
AUTH_KEY = f"{GIGA_PART_1}{GIGA_PART_2}"

token_cache = {"token": "", "expires_at": 0}
chat_histories = {}


def get_token():
    now = time.time()
    if token_cache["token"] and now < token_cache["expires_at"] - 60:
        return token_cache["token"], ""
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
            return token_cache["token"], ""
        return "", f"HTTP {res.status_code}: {res.text[:150]}"
    except Exception as e:
        return "", f"Сбой сети: {e}"


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])
    token, err = get_token()
    if not token:
        return f"⚠️ Ошибка GigaChat: {err}"

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
        return f"⚠️ Ошибка ответа GigaChat: HTTP {res.status_code}"
    except Exception as e:
        return f"⚠️ Сбой запроса к GigaChat: {e}"
