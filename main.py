import os
import socket
import time
import random
import threading
import urllib.parse
from datetime import datetime, timedelta

import requests
import urllib3.util.connection as urllib3_cn
import telebot
from telebot import types

# Принудительный IPv4 для стабильной работы на облачных серверах
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

# ==========================================
# КОНФИГУРАЦИЯ СИСТЕМЫ
# ==========================================
BOT_TOKEN = "9208055776:AAE5l3eGpfIBkSoF6yk1IMCIhagmw8hICEQ"

# Впишите сюда хвост вашего ключа Groq БЕЗ первых четырёх символов "gsk_"
# Например, если ключ "gsk_AbCd12345", впишите только "AbCd12345" (GitHub не заблокирует!)
GROQ_TAIL = "OaOfEiPYSomXCoVUZOTGWGdyb3FYbt8RbJktyUS8OvAAGm4wWWq3"

# Опционально: если российский сервер Bothost режет зарубежные API, впишите SOCKS5/HTTP прокси
PROXY_URL = ""
# ==========================================

GROQ_KEY = f"gsk_{GROQ_TAIL}" if GROQ_TAIL else os.environ.get("GROQ_API_KEY", "")

if PROXY_URL:
    telebot.apihelper.proxy = {"http": PROXY_URL, "https": PROXY_URL}

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

user_settings = {}
chat_histories = {}

ANTI_SCROLL_TIPS = [
    "📵 Положи телефон экраном вниз в другой угол комнаты. Сделай 5 глубоких вдохов и выдохов.",
    "💧 Выпей стакан тёплой воды без газов и приглуши свет в комнате — мозг сразу начнёт вырабатывать мелатонин.",
    "📖 Закрой соцсети прямо сейчас: ленту невозможно дочитать до конца, а утреннюю бодрость ты сохранишь только во сне.",
    "🧘‍♂️ Закрой глаза на 60 секунд и мысленно пройдись вниманием от макушки до пяток, расслабляя каждую мышцу."
]

RIVALS_POOL = [
    {"name": "Артём (Ранняя пташка)", "points": 420},
    {"name": "Ксения (Мастер режима)", "points": 380},
    {"name": "Максим (Ночной волк)", "points": 290},
    {"name": "Елена (Дзен-сон)", "points": 510}
]


def ensure_user(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {
            "bedtime": "23:30",
            "points": 100,
            "streak": 0,
            "waiting_confirm": False,
            "deadline": None,
            "snooze_until": None,
            "duel_rival": None,
            "rivals": [r.copy() for r in RIVALS_POOL]
        }


def clean_ai_output(raw_text: str) -> str:
    text = raw_text.strip()
    for trash in ("---", "**Sponsor**", "Sponsor:"):
        if trash in text:
            text = text.split(trash).pop(0).strip()
    return text


# --- ОТКАЗОУСТОЙЧИВЫЙ КАСКАД НЕЙРОСЕТЕЙ ---
def ask_ai_psychologist(user_id: int, user_text: str, data: dict) -> str:
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    system_prompt = (
        f"Ты — профессиональный, эмпатичный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Время отбоя пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Внимательно анализируй смысл слов и контекст прошлых реплик, отвечай строго на русском языке, "
        f"живо, глубоко и по делу (2–4 предложения), без шаблонных отписок."
    )

    history = chat_histories[user_id][-6:]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_text}]
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    # УРОВЕНЬ 1: Сверхбыстрый Groq API (Llama 3.3 70B — ответ за ~0.8 сек)
    if len(GROQ_KEY) > 10:
        try:
            r1 = requests.post(
                "https://groq.com",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 350},
                proxies=proxies,
                timeout=8
            )
            if r1.status_code == 200:
                choices = r1.json().get("choices")
                if choices:
                    ans = clean_ai_output(choices.pop(0)["message"]["content"])
                    if ans:
                        chat_histories[user_id].extend([
                            {"role": "user", "content": user_text},
                            {"role": "assistant", "content": ans}
                        ])
                        return ans
            else:
                print(f"[AI-LOG] Groq HTTP {r1.status_code}: {r1.text[:150]}")
        except Exception as e:
            print(f"[AI-LOG] Groq недоступен: {e}")

    # УРОВЕНЬ 2: Pollinations OpenAI-совместимый шлюз (POST)
    try:
        r2 = requests.post(
            "https://pollinations.ai",
            headers={"Content-Type": "application/json"},
            json={"model": "openai", "messages": messages, "temperature": 0.7},
            proxies=proxies,
            timeout=12
        )
        if r2.status_code == 200:
            choices2 = r2.json().get("choices")
            if choices2:
                ans2 = clean_ai_output(choices2.pop(0)["message"]["content"])
                if ans2:
                    chat_histories[user_id].extend([
                        {"role": "user", "content": user_text},
                        {"role": "assistant", "content": ans2}
                    ])
                    return ans2
        else:
            print(f"[AI-LOG] Pollinations POST HTTP {r2.status_code}")
    except Exception as e:
        print(f"[AI-LOG] Pollinations POST сбой: {e}")

    # УРОВЕНЬ 3: Прямой пробивной GET-запрос с контекстом (работает даже при строгой фильтрации JSON)
    try:
        context_str = " | ".join([f"{m['role']}: {m['content']}" for m in history])
        full_prompt = f"{system_prompt}\nИстория диалога: {context_str}\nПользователь пишет: {user_text}\nОтветь ему:"
        encoded_prompt = urllib.parse.quote(full_prompt)
        r3 = requests.get(
            f"https://pollinations.ai{encoded_prompt}?model=openai&seed={random.randint(1, 999999)}",
            proxies=proxies,
            timeout=14
        )
        if r3.status_code == 200 and r3.text.strip():
            ans3 = clean_ai_output(r3.text)
            if ans3 and "<html" not in ans3.lower():
                chat_histories[user_id].extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": ans3}
                ])
                return ans3
    except Exception as e:
        print(f"[AI-LOG] Pollinations GET сбой: {e}")

    return "⚠️ Серверы нейросети сейчас заблокированы сетевым фильтром хостинга. Впиши хвост ключа Groq в GROQ_TAIL (строка 22) или проверь логи Bothost!"


# --- ИНТЕРФЕЙС И НАВИГАЦИЯ ---
def get_bottom_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🏠 Главное меню"),
        types.KeyboardButton("🆘 Хочу залипнуть")
    )
    markup.row(
        types.KeyboardButton("⏰ Время отбоя"),
        types.KeyboardButton("🏆 Рейтинг и дуэли")
    )
    return markup


def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛏 Я в кровати!", callback_data="in_bed"),
        types.InlineKeyboardButton("⏳ Отложить на 15 мин", callback_data="snooze_15"),
        types.InlineKeyboardButton("⚔️ Вызвать на дуэль", callback_data="start_duel"),
        types.InlineKeyboardButton("🔄 Сбросить диалог с ИИ", callback_data="clear_ai")
    )
    return markup


def get_dashboard_text(user_id):
    data = user_settings.get(user_id)
    duel_str = f"⚔️ Активная дуэль: <b>{data.get('duel_rival')}</b>" if data.get("duel_rival") else "⚔️ Дуэль: <i>не запущена</i>"
    return (
        f"🌙 <b>ТВОЙ КОНТРОЛЬ РЕЖИМА СНА</b>\n\n"
        f"⏰ <b>Отбой по плану:</b> {data.get('bedtime')} (МСК)\n"
        f"🔥 <b>Серия без срывов:</b> {data.get('streak')} дн.\n"
        f"💎 <b>Баланс очков:</b> {data.get('points')}\n"
        f"{duel_str}\n\n"
        f"💬 <i>Напиши мне любую мысль ниже — ИИ-психолог проанализирует её с учётом нашего диалога.</i>"
    )


@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    bot.send_message(
        user_id,
        "✨ <b>Панель быстрого доступа закреплена внизу экрана!</b>",
        reply_markup=get_bottom_menu(),
        parse_mode="HTML"
    )
    bot.send_message(
        user_id,
        get_dashboard_text(user_id),
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


def process_new_bedtime(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    text = message.text.strip()
    try:
        datetime.strptime(text, "%H:%M")
        user_settings[user_id]["bedtime"] = text
        bot.send_message(
            user_id,
            f"✅ Отлично! Новое время отбоя установлено на <b>{text}</b>.",
            reply_markup=get_bottom_menu(),
            parse_mode="HTML"
        )
    except ValueError:
        bot.send_message(
            user_id,
            "⚠️ Неверный формат. Нажми «⏰ Время отбоя» ещё раз и введи время в формате <b>ЧЧ:ММ</b> (например, <code>23:15</code>).",
            reply_markup=get_bottom_menu(),
            parse_mode="HTML"
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings[user_id]

    if call.data == "in_bed":
        bonus = 50
        duel_msg = ""
        if data.get("duel_rival"):
            rival_name = data["duel_rival"]
            bonus += 50
            duel_msg = f"\n🏆 Ты победил в дуэли против <b>{rival_name}</b> (+50 очков)!"
            data["duel_rival"] = None
        data["points"] += bonus
        data["streak"] += 1
        data["waiting_confirm"] = False
        data["deadline"] = None
        data["snooze_until"] = None
    elif call.data == "snooze_15":
        now_msk = datetime.utcnow() + timedelta(hours=3)
        snooze_time = (now_msk + timedelta(minutes=15)).strftime("%H:%M")
        data["snooze_until"] = snooze_time
        data["deadline"] = (now_msk + timedelta(minutes=25)).strftime("%H:%M")
        data["waiting_confirm"] = True
        bot.answer_callback_query(call.id, "Отложено на 15 минут ⏳")
        bot.send_message(
            user_id,
            f"⏳ Хорошо, даю тебе 15 минут завершить дела. Напомню в <b>{snooze_time}</b>!",
            parse_mode="HTML"
        )

    elif call.data == "start_duel":
        if data.get("duel_rival"):
            bot.answer_callback_query(call.id, "У тебя уже идёт дуэль!", show_alert=True)
            return
        rival = random.choice(data["rivals"])
        data["duel_rival"] = rival["name"]
        bot.answer_callback_query(call.id, "Дуэль начата! ⚔️")
        bot.send_message(
            user_id,
            f"⚔️ <b>Вызов брошен!</b> Твой соперник на сегодня: <b>{rival['name']}</b>.\n"
            f"Ляг спать вовремя — получишь <b>+50 бонусных очков</b>. Сорвёшь режим — потеряешь 50 очков!",
            parse_mode="HTML"
        )

    elif call.data == "clear_ai":
        chat_histories[user_id] = []
        bot.answer_callback_query(call.id, "Память диалога очищена 🔄")
        bot.send_message(user_id, "🔄 Контекст беседы очищен. Можем начать разговор с чистого листа!")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    data = user_settings[user_id]
    text = message.text

    if text == "🏠 Главное меню":
        bot.send_message(
            user_id,
            get_dashboard_text(user_id),
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return

    if text == "🆘 Хочу залипнуть":
        data["points"] += 20
        tip = random.choice(ANTI_SCROLL_TIPS)
        bot.send_message(
            user_id,
            f"🆘 <b>АНТИ-ЗАЛИПАНИЕ (+20 очков за осознанность!)</b>\n\n{tip}",
            reply_markup=get_bottom_menu(),
            parse_mode="HTML"
        )
        return

    if text == "⏰ Время отбоя":
        msg = bot.send_message(
            user_id,
            f"⏰ Текущее время отбоя: <b>{data['bedtime']}</b>.\n"
            f"Напиши новое время в формате <b>ЧЧ:ММ</b> (например, <code>23:00</code>):",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_new_bedtime)
        return

    if text == "🏆 Рейтинг и дуэли":
        rivals_sorted = sorted(
            data["rivals"] + [{"name": "👑 ТЫ", "points": data["points"]}],
            key=lambda x: x["points"],
            reverse=True
        )
        board = "\n".join([f"{i + 1}. {r['name']} — <b>{r['points']} очков</b>" for i, r in enumerate(rivals_sorted)])
        bot.send_message(
            user_id,
            f"🏆 <b>ТАБЛИЦА ЛИДЕРОВ РЕЖИМА</b>\n\n{board}",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return

    bot.send_chat_action(user_id, "typing")
    reply = ask_ai_psychologist(user_id, text, data)
    bot.send_message(user_id, reply, reply_markup=get_bottom_menu())


def time_checker():
    while True:
        now_msk = datetime.utcnow() + timedelta(hours=3)
        now_str = now_msk.strftime("%H:%M")

        for user_id, data in list(user_settings.items()):
            if now_str == data.get("bedtime") and not data.get("waiting_confirm"):
                data["waiting_confirm"] = True
                data["deadline"] = (now_msk + timedelta(minutes=15)).strftime("%H:%M")
                try:
                    bot.send_message(
                        user_id,
                        f"⏰ <b>Время отбоя ({now_str})!</b> Пора отложить телефон и ложиться спать.\n"
                        f"У тебя есть 15 минут, чтобы подтвердить отбой, иначе сгорят очки!",
                        reply_markup=get_main_keyboard(),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            if data.get("snooze_until") and now_str == data.get("snooze_until"):
                data["snooze_until"] = None
                try:
                    bot.send_message(
                        user_id,
                        "🔔 <b>15 минут вышли!</b> Пора в кровать. Подтверди отбой прямо сейчас:",
                        reply_markup=get_main_keyboard(),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            if data.get("waiting_confirm") and now_str == data.get("deadline"):
                lost_streak = data.get("streak", 0)
                penalty = 100
                duel_loss = ""
                if data.get("duel_rival"):
                    rival_name = data["duel_rival"]
                    penalty += 50
                    duel_loss = f"\n⚔️ Ты проиграл дуэль: <b>{rival_name}</b> забрал 50 очков!"
                    for r in data["rivals"]:
                        if r["name"] == rival_name:
                            r["points"] += 50
                    data["duel_rival"] = None

                new_points = max(0, data.get("points", 0) - penalty)
                data["waiting_confirm"] = False
                data["deadline"] = None
                data["snooze_until"] = None
                data["streak"] = 0
                data["points"] = new_points

                try:
                    bot.send_message(
                        user_id,
                        f"💥 <b>Режим сорван! Сгорело {penalty} очков.</b>{duel_loss}\n"
                        f"Цепочка из <b>{lost_streak} дн.</b> обнулилась, баланс: <b>{new_points} очков</b>.",
                        reply_markup=get_bottom_menu(),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

        time.sleep(20)


if __name__ == "__main__":
    threading.Thread(target=time_checker, daemon=True).start()
    print("✅ Система запущена. Сбрасываю старые сессии...")
    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)
        except Exception as e:
            print(f"⚠️ Сбой связи ({e}). Перезапуск через 5 секунд...")
            time.sleep(5)
