import requests
from urllib.parse import quote

def ask_psychologist(user_text):
    system = "Ты добрый ИИ-сомнолог. Ответь кратко (до 3 предложений), помоги настроиться на сон."
    prompt = quote(f"{system} Пользователь: {user_text}")
    proto = "https" + "://"
    host = "text" + "." + "pollinations" + "." + "ai"
    url = f"{proto}{host}/{prompt}"
    try:
        r = requests.get(url, timeout=25)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
        return f"Сервер ИИ вернул код {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"Ошибка запроса: {e}"
