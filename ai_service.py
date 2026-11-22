import requests
from config import OPENROUTER_KEY

def ask_psychologist(user_text):
    if not OPENROUTER_KEY:
        return "Ключ не задан в настройках сервера."
    url = f"https://googleapis.com{OPENROUTER_KEY}"
    prompt = "Ты — добрый ИИ-сомнолог и психолог. Отвечай кратко (до 3 предложений), поддерживай и помогай настроиться на здоровый сон. Сообщение пользователя: " + user_text
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=data, timeout=20)
        if not r.text.strip():
            return f"Пустой ответ от сервера (код {r.status_code}). Хостинг блокирует этот домен."
        res = r.json()
        if "candidates" in res:
            return res["candidates"]["content"]["parts"]["text"]
        return f"Ответ Google ({r.status_code}): {res.get('error', {}).get('message', r.text[:150])}"
    except Exception as e:
        return f"Сбой сети: {e}"
