import requests
from config import OPENROUTER_KEY, AI_MODEL

def ask_psychologist(user_text):
    if not OPENROUTER_KEY:
        return "ИИ-психолог временно отдыхает (не задан ключ). Но помни: лучший отдых — лечь вовремя!"
    url = "https://openrouter.ai"
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    prompt = "Ты — добрый ИИ-сомнолог и психолог в Telegram-боте. Отвечай кратко (до 3 предложений), поддерживай и помогай настроиться на здоровый сон."
    data = {
        "model": AI_MODEL,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_text}]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=15).json()
        return res["choices"][0]["message"]["content"]
    except Exception:
        return "Сейчас сервер мыслей перегружен, но я рядом. Выключи экраны и сделай пару глубоких вдохов."
