from openai import OpenAI

GROQ_TAIL = "OaOfEiPYSomXCoVUZOTGWGdyb3FYbt8RbJktyUS8OvAAGm4wWWq3"
GROQ_KEY = f"gsk_{GROQ_TAIL}".strip()

client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://groq.com"
)

chat_histories = {}


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])

    prompt = (
        f"Ты — профессиональный, бережный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Отбой пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Отвечай строго на русском языке, тепло, глубоко и по делу (2–4 предложения), учитывая прошлые сообщения."
    )
    messages = [{"role": "system", "content": prompt}] + chat_histories[user_id][-6:] + [{"role": "user", "content": user_text}]

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=350
        )
        reply = completion.choices.pop(0).message.content.strip()
        if reply:
            chat_histories[user_id].extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": reply}
            ])
            return reply
    except Exception as e:
        return f"⚠️ Ошибка Groq SDK: {e}"

    return "🌙 Я рядом. Расскажи подробнее, что мешает тебе расслабиться перед сном?"
