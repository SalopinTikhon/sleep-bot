import telebot
from telebot import types
import requests
import random
import threading
import time
from datetime import datetime, timedelta

# Вставьте сюда токен вашего ПЕРВОГО бота (трекера сна)
BOT_TOKEN = "9208055776:AAE5l3eGpfIBkSoF6yk1IMCIhagmw8hICEQ"

bot = telebot.TeleBot(BOT_TOKEN)

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

GROQ_KEY = ""

def ask_ai_psychologist(user_id, user_text, data):
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    system_prompt = (
        f"Ты — профессиональный, эмпатичный ИИ-психолог и специалист по гигиене сна, созданный для помощи в настройке "
        f"здорового режима и отказа от ночного залипания в телефоне. "
        f"Время отбоя пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Внимательно анализируй контекст прошлых сообщений, отвечай глубоко, тепло и по делу (3–5 предложений)."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_histories[user_id][-6:])
    messages.append({"role": "user", "content": user_text})

    # 1. Пробуем сверхбыстрый Groq API
    try:
        response = requests.post(
            "https://groq.com",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 400},
            timeout=8
        )
        if response.status_code == 200:
            choices = response.json().get("choices")
            if choices:
                reply = choices[0]["message"]["content"].strip()
                chat_histories[user_id].append({"role": "user", "content": user_text})
                chat_histories[user_id].append({"role": "assistant", "content": reply})
                return reply
        else:
            print(f"Groq статус {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Groq недоступен с IP сервера: {e}")

    # 2. Резервный канал (если IP сервера в РФ заблокирован Groq)
    try:
        res2 = requests.post(
            "https://pollinations.ai",
            json={"model": "openai", "messages": messages, "temperature": 0.7},
            timeout=12
        )
        if res2.status_code == 200:
            choices2 = res2.json().get("choices")
            if choices2:
                reply2 = choices2[0]["message"]["content"].strip()
                chat_histories[user_id].append({"role": "user", "content": user_text})
                chat_histories[user_id].append({"role": "assistant", "content": reply2})
                return reply2
    except Exception as e:
        print(f"Ошибка резервного ИИ: {e}")

    return "🌙 Я рядом. Расскажи подробнее, что сейчас мешает тебе расслабиться перед сном?"

# --- ПОСТОЯННАЯ НИЖНЯЯ ПАНЕЛЬ НАВИГАЦИИ ---
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
        f"💬 <i>Просто напиши мне любое сообщение ниже, если не можешь уснуть или тревожишься — ИИ-психолог сразу поддержит тебя.</i>"
    )

@bot.message_handler(commands=['start', 'menu'])
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

# --- ОБРАБОТКА ВВОДА НОВОГО ВРЕМЕНИ ОТБОЯ ---
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
            "⚠️ Неверный формат. Нажми «⏰ Время отбоя» ещё раз и введи время строго в формате <b>ЧЧ:ММ</b> (например, <code>23:15</code>).",
            reply_markup=get_bottom_menu(),
            parse_mode="HTML"
        )

# --- INLINE-КНОПКИ ПОД СООБЩЕНИЯМИ ---
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
        bot.answer_callback_query(call.id, "Молодец! Спокойной ночи 🌙")
        bot.send_message(
            user_id,
            f"🛌 <b>Режим соблюдён! +{bonus} очков.</b>{duel_msg}\n"
            f"Твоя серия: <b>{data['streak']} дн.</b>, баланс: <b>{data['points']} очков</b>. Спокойной ночи! ✨",
            parse_mode="HTML"
        )

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

# --- ОБРАБОТКА НИЖНЕЙ ПАНЕЛИ И ЖИВОГО ЧАТА С ИИ ---
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
        board = "\n".join([f"{i+1}. {r['name']} — <b>{r['points']} очков</b>" for i, r in enumerate(rivals_sorted)])
        bot.send_message(
            user_id,
            f"🏆 <b>ТАБЛИЦА ЛИДЕРОВ РЕЖИМА</b>\n\n{board}",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return

    # Если нажата не кнопка меню — отвечает ИИ-психолог
    bot.send_chat_action(user_id, 'typing')
    reply = ask_ai_psychologist(user_id, text, data)
    bot.send_message(user_id, reply, reply_markup=get_bottom_menu())

# --- ФОНОВЫЙ ТАЙМЕР КОНТРОЛЯ ОТБОЯ (МСК) ---
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

print("✅ Бот контроля сна с нижней панелью и ИИ-психологом запущен!")

while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)
    except Exception as e:
        print(f"⚠️ Временный обрыв связи с Telegram ({e}). Переподключаюсь через 5 секунд...")
        time.sleep(5)
