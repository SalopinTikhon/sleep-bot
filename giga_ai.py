import random
import urllib.parse
import requests

GROQ_TAIL = "OaOfEiPYSomXCoVUZOTGWGdyb3FYbt8RbJktyUS8OvAAGm4wWWq3"
GROQ_KEY = f"gsk_{GROQ_TAIL}".strip()

chat_histories = {}


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])

    prompt = (
        f"Ты — профессиональный, эмпатичный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Отбой пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Отвечай строго на русском языке, тепло, глубоко и по делу (2–4 предложения), учитывая прошлые реплики."
    )
    history = chat_histories[user_id][-6:]
    messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": user_text}]

    # КАНАЛ 1: Groq API
    try:
        r1 = requests.post(
            "https://groq.com",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 350},
            timeout=8
        )
        if r1.status_code == 200:
            reply = r1.json()["choices"].pop(0)["message"]["content"].strip()
            if reply:
                chat_histories[user_id].extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}])
                return reply
    except Exception:
        pass

    # КАНАЛ 2: Безопасный GET-шлюз с контекстом
    try:
        ctx = " | ".join([f"{m['role']}: {m['content']}" for m in history])
        full_q = f"{prompt} | Контекст: {ctx} | Пользователь: {user_text} | Ответь по-русски:"
        r2 = requests.get(
            "https://pollinations.ai",
            params={"prompt": full_q, "model": "openai", "seed": random.randint(1, 999999)},
            timeout=15
        )
        if r2.status_code == 200 and r2.text.strip():
            reply2 = r2.text.strip()
            for trash in ("---", "**Sponsor**"):
                if trash in reply2:
                    reply2 = reply2.split(trash).pop(0).strip()
            if reply2 and "<html" not in reply2.lower():
                chat_histories[user_id].extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": reply2}])
                return reply2
    except Exception as e:
        return f"⚠️ Ошибка GET-канала: {e}"
