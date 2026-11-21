import uuid
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGA_PART_1 = "MDE5ZTIwOWQtNmI1NC03YzlmLWJhZDQ" + "tMTUxMzA3YWY1MDYz"
GIGA_PART_2 = "OjdlZjE4NGY1LThkMGQtNGNmNS1iNjJlLWVhM2NiZWQyNzcxNQ=="
AUTH_KEY = f"{GIGA_PART_1}{GIGA_PART_2}"

token_cache = {"token": "", "expires_at": 0}
chat_histories = {}


def get_token() -> str:
    now = time.time()
    if token_cache["token"] and now < token_cache["expires_at"] - 60:
        return token_cache["token"]
    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {AUTH_KEY}"
            },
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False,
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            token_cache["token"] = data.get("access_token", "")
            token_cache["expires_at"] = (data.get("expires_at", 0) / 1000.0) or (now + 1700)
            return token_cache["token"]
        print(f"[GIGACHAT-AUTH] HTTP {res.status_code}: {res.text[:150]}")
    except Exception as e:
        print(f"[GIGACHAT-AUTH] Сбой: {e}")
    return ""


def ask_psychologist(user_id: int, user_text: str, data: dict) -> str:
    chat_histories.setdefault(user_id, [])
    token = get_token()
    if not token:
        return "⚠️ Не удалось подключиться к GigaChat. Проверьте ключ в giga_ai.py."

    prompt = (
        f"Ты — профессиональный, бережный ИИ-психолог и коуч по гигиене сна, созданный для настройки "
        f"здорового режима дня и отказа от ночного залипания в телефоне. "
        f"Отбой пользователя: {data.get('bedtime')}, серия без срывов: {data.get('streak')} дн. "
        f"Отвечай строго на русском языке, тепло, глубоко и по делу (2–4 предложения), учитывая прошлые сообщения."
    )
    messages = [{"role": "system", "content": prompt}] + chat_histories[user_id][-6:] + [{"role": "user", "content": user_text}]

    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"model": "GigaChat", "messages": messages, "temperature": 0.7, "max_tokens": 350},
            verify=False,
            timeout=12
        )
        if res.status_code == 200:
            reply = res.json()["choices"].pop(0)["message"]["content"].strip()
            if reply:
                chat_histories[user_id].extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": reply}
                ])
                return reply
        print(f"[GIGACHAT-CHAT] HTTP {res.status_code}: {res.text[:150]}")
    except Exception as e:
        print(f"[GIGACHAT-CHAT] Сбой: {e}")

    return "🌙 Я рядом и слушаю тебя. Расскажи подробнее, что мешает тебе расслабиться перед сном?"
from telebot import types


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
import socket
import time
import random
import threading
from datetime import datetime, timedelta
import urllib3.util.connection as urllib3_cn
import telebot

from giga_ai import ask_psychologist, chat_histories
from keyboards import get_bottom_menu, get_main_keyboard

urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

BOT_TOKEN = "9208055776:AAE5l3eGpfIBkSoF6yk1IMCIhagmw8hICEQ"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)
user_settings = {}

ANTI_SCROLL_TIPS = [
    "📵 Положи телефон экраном вниз в другой угол комнаты. Сделай 5 глубоких вдохов.",
    "💧 Выпей стакан тёплой воды и приглуши свет в комнате.",
    "📖 Закрой соцсети прямо сейчас: утреннюю бодрость ты сохранишь только во сне."
]

RIVALS_POOL = [
    {"name": "Артём (Ранняя пташка)", "points": 420},
    {"name": "Ксения (Мастер режима)", "points": 380},
    {"name": "Максим (Ночной волк)", "points": 290}
]


def ensure_user(uid):
    if uid not in user_settings:
        user_settings[uid] = {
            "bedtime": "23:30", "points": 100, "streak": 0,
            "waiting_confirm": False, "deadline": None, "snooze_until": None,
            "duel_rival": None, "rivals": [r.copy() for r in RIVALS_POOL]
        }


def dashboard_text(uid):
    d = user_settings[uid]
    duel = f"⚔️ Дуэль: <b>{d['duel_rival']}</b>" if d["duel_rival"] else "⚔️ Дуэль: <i>нет</i>"
    return (
        f"🌙 <b>КОНТРОЛЬ РЕЖИМА СНА</b>\n\n"
        f"⏰ <b>Отбой:</b> {d['bedtime']} (МСК)\n🔥 <b>Серия:</b> {d['streak']} дн.\n"
        f"💎 <b>Очки:</b> {d['points']}\n{duel}\n\n"
        f"💬 <i>Напиши любую мысль — ИИ-психолог GigaChat ответит с учётом диалога.</i>"
    )


@bot.message_handler(commands=["start", "menu"])
def cmd_start(m):
    ensure_user(m.from_user.id)
    bot.send_message(m.from_user.id, "✨ <b>Меню закреплено внизу!</b>", reply_markup=get_bottom_menu(), parse_mode="HTML")
    bot.send_message(m.from_user.id, dashboard_text(m.from_user.id), reply_markup=get_main_keyboard(), parse_mode="HTML")


def set_bedtime(m):
    uid = m.from_user.id
    try:
        datetime.strptime(m.text.strip(), "%H:%M")
        user_settings[uid]["bedtime"] = m.text.strip()
        bot.send_message(uid, f"✅ Отбой установлен на <b>{m.text.strip()}</b>.", reply_markup=get_bottom_menu(), parse_mode="HTML")
    except ValueError:
        bot.send_message(uid, "⚠️ Формат должен быть <b>ЧЧ:ММ</b> (например, <code>23:15</code>).", reply_markup=get_bottom_menu(), parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid = c.from_user.id
    ensure_user(uid)
    d = user_settings[uid]
    if c.data == "in_bed":
        bonus = 100 if d["duel_rival"] else 50
        d["duel_rival"] = None
        d["points"] += bonus
        d["streak"] += 1
        d["waiting_confirm"] = False
        bot.answer_callback_query(c.id, "Спокойной ночи! 🌙")
        bot.send_message(uid, f"🛌 <b>Режим соблюдён! +{bonus} очков.</b> Серия: {d['streak']} дн.", parse_mode="HTML")
    elif c.data == "snooze_15":
        now = datetime.utcnow() + timedelta(hours=3)
        d["snooze_until"] = (now + timedelta(minutes=15)).strftime("%H:%M")
        d["deadline"] = (now + timedelta(minutes=25)).strftime("%H:%M")
        d["waiting_confirm"] = True
        bot.answer_callback_query(c.id, "Отложено на 15 мин ⏳")
        bot.send_message(uid, f"⏳ Напомню в <b>{d['snooze_until']}</b>!", parse_mode="HTML")
    elif c.data == "start_duel":
        rival = random.choice(d["rivals"])
        d["duel_rival"] = rival["name"]
        bot.answer_callback_query(c.id, "Дуэль начата! ⚔️")
        bot.send_message(uid, f"⚔️ Соперник: <b>{rival['name']}</b>! Ставка: 50 очков.", parse_mode="HTML")
    elif c.data == "clear_ai":
        chat_histories[uid] = []
        bot.answer_callback_query(c.id, "Память очищена 🔄")
        bot.send_message(uid, "🔄 Диалог с ИИ начат с чистого листа!")


@bot.message_handler(func=lambda m: True)
def messages(m):
    uid = m.from_user.id
    ensure_user(uid)
    d = user_settings[uid]
    if m.text == "🏠 Главное меню":
        bot.send_message(uid, dashboard_text(uid), reply_markup=get_main_keyboard(), parse_mode="HTML")
    elif m.text == "🆘 Хочу залипнуть":
        d["points"] += 20
        bot.send_message(uid, f"🆘 <b>+20 очков!</b>\n\n{random.choice(ANTI_SCROLL_TIPS)}", reply_markup=get_bottom_menu(), parse_mode="HTML")
    elif m.text == "⏰ Время отбоя":
        msg = bot.send_message(uid, f"⏰ Сейчас: <b>{d['bedtime']}</b>. Введи новое время (<b>ЧЧ:ММ</b>):", parse_mode="HTML")
        bot.register_next_step_handler(msg, set_bedtime)
    elif m.text == "🏆 Рейтинг и дуэли":
        top = sorted(d["rivals"] + [{"name": "👑 ТЫ", "points": d["points"]}], key=lambda x: x["points"], reverse=True)
        board = "\n".join([f"{i + 1}. {r['name']} — <b>{r['points']}</b>" for i, r in enumerate(top)])
        bot.send_message(uid, f"🏆 <b>РЕЙТИНГ</b>\n\n{board}", reply_markup=get_main_keyboard(), parse_mode="HTML")
    else:
        bot.send_chat_action(uid, "typing")
        bot.send_message(uid, ask_psychologist(uid, m.text, d), reply_markup=get_bottom_menu())


def timer():
    while True:
        now = (datetime.utcnow() + timedelta(hours=3)).strftime("%H:%M")
        for uid, d in list(user_settings.items()):
            if now == d["bedtime"] and not d["waiting_confirm"]:
                d["waiting_confirm"] = True
                d["deadline"] = (datetime.utcnow() + timedelta(hours=3, minutes=15)).strftime("%H:%M")
                try:
                    bot.send_message(uid, f"⏰ <b>Время отбоя ({now})!</b> Подтверди в меню:", reply_markup=get_main_keyboard(), parse_mode="HTML")
                except Exception:
                    pass
            elif d["snooze_until"] == now:
                d["snooze_until"] = None
                try:
                    bot.send_message(uid, "🔔 <b>15 минут вышли!</b> Пора спать:", reply_markup=get_main_keyboard(), parse_mode="HTML")
                except Exception:
                    pass
            elif d["waiting_confirm"] and d["deadline"] == now:
                d["waiting_confirm"] = False
                d["streak"] = 0
                d["points"] = max(0, d["points"] - 100)
                try:
                    bot.send_message(uid, f"💥 <b>Режим сорван!</b> Баланс: {d['points']} очков.", reply_markup=get_bottom_menu(), parse_mode="HTML")
                except Exception:
                    pass
        time.sleep(20)


if __name__ == "__main__":
    threading.Thread(target=timer, daemon=True).start()
    print("✅ Бот с GigaChat запущен!")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception:
            time.sleep(5)
