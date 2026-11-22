import requests
from urllib.parse import quote

def ask_psychologist(user_text):
    system_prompt = "Ты — добрый ИИ-сомнолог и психолог. Отвечай кратко (до 3 предложений), поддерживай и помогай настроиться на здоровый сон."
    full_prompt = f"{system_prompt}\nПользователь: {user_text}\nПсихолог:"
    url = f"https://pollinations.ai{quote(full_prompt)}?model=openai"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
        return f"Сервер ИИ временно занят (код {r.status_code}). Попробуй через минуту."
    except Exception as e:
        return f"Ошибка соединения: {type(e).__name__}"
