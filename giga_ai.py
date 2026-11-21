import requests

GROQ_TAIL = "OaOfEiPYSomXCoVUZOTGWGdyb3FYbt8RbJktyUS8OvAAGm4wWWq3"
GROQ_KEY = f"gsk_{GROQ_TAIL}".strip()

chat_histories = {}


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])

    prompt = (
        f"Ты — профессиональный, бережный ИИ-психолог и коуч по гигиене сна. "
        f"Отбой пользователя: {data.get('bedtime')}, серия: {data.get('streak')} дн. "
        f"Отвечай строго по-русски, тепло, осмысленно и по делу (2–4 предложения), учитывая прошлые сообщения."
    )
    history = chat_histories[user_id][-6:]
    messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": user_text}]

    try:
        r = requests.post(
            "https://groq.com",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.7, "max_tokens": 350},
            timeout=10
        )
        if r.status_code == 200:
            reply = r.json()["choices"].pop(0)["message"]["content"].strip()
            if reply:
                chat_histories[user_id].extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}])
                return reply
        return f"⚠️ Groq статус {r.status_code}: {r.text[:150]}"
    except Exception as e:
        return f"⚠️ Groq сбой: {e}"
