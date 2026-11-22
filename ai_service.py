import time, requests
from urllib.parse import quote

def ask_psychologist(user_text):
    system = "Ты добрый ИИ-сомнолог. Ответь кратко (до 3 предложений), помоги настроиться на сон."
    prompt = quote(f"{system} Пользователь: {user_text}")
    proto = "https" + "://"
    host = "text" + "." + "pollinations" + "." + "ai"
    url = f"{proto}{host}/{prompt}"
    for _ in range(2):
        try:
            r = requests.get(url, timeout=25)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
            if r.status_code == 402:
                time.sleep(5)
                continue
        except Exception:
            pass
    return "Сейчас я немного задумался, но мой главный совет на сегодня: отложи телефон, приглуши свет и сделай 5 глубоких вдохов. Спокойной ночи!"
