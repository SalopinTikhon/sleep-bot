import g4f

chat_histories = {}


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])

    prompt = (
        f"Ты — профессиональный, бережный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Отбой пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Отвечай строго на русском языке, тепло, глубоко и по делу (2–4 предложения), учитывая прошлые реплики."
    )
    history = chat_histories[user_id][-6:]
    messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": user_text}]

    for model_name in ("gpt-4o-mini", "llama-3.3-70b", "qwen-2.5-72b"):
        try:
            response = g4f.ChatCompletion.create(
                model=model_name,
                messages=messages
            )
            reply = str(response).strip()
            if reply and len(reply) > 5 and "error" not in reply.lower()[:20]:
                chat_histories[user_id].extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": reply}
                ])
                return reply
        except Exception as e:
            print(f"[G4F-{model_name}] Сбой: {e}")

    return "🌙 Я рядом и внимательно слушаю тебя. Расскажи подробнее, что мешает тебе расслабиться перед сном?"
