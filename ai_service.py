import requests
from config import OPENROUTER_KEY, AI_MODEL

def ask_psychologist(user_text):
    if not OPENROUTER_KEY:
        return "Ошибка: ключ OpenRouter пустой (проверь OR_KEY_1 и OR_KEY_2)."
    url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me",
        "X-Title": "SleepBot"
    }
    prompt = "Ты — добрый ИИ-сомнолог и психолог. Отвечай кратко (до 3 предложений), поддерживай и помогай настроиться на здоровый сон."
    data = {"model": AI_MODEL, "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_text}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        res = r.json()
        if "choices" in res:
            return res["choices"]["message"]["content"]
        return f"Ответ API ({r.status_code}): {res.get('error', {}).get('message', str(res))}"
    except Exception as e:
        return f"Сбой сети: {e}"
