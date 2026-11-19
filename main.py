import sys
import time
import random
import urllib.parse
import threading
from datetime import datetime, timedelta, timezone
import requests
import telebot
from telebot import types

sys.stdout.reconfigure(line_buffering=True)

# Вставьте сюда ваш токен от @BotFather внутри кавычек
TOKEN = "9208055776:AAE5l3eGpfIBkSoF6yk1IMCIhagmw8hICEQ"
bot = telebot.TeleBot(TOKEN)

MSK = timezone(timedelta(hours=3))

def get_msk_now():
    return datetime.now(MSK)

user_settings = {}

RIVAL_NAMES = (
    "Алексей К.",
    "Марина_МСК",
    "Дмитрий (IT)",
    "Алина С.",
    "Макс_04",
    "Елена В."
)

ANTI_SCROLL_TIPS = (
    "🧠 <b>Психологический факт:</b> Бесконечная лента работает как игровой автомат. Мозг ждет «джекпот» в следующем видео, но вместо радости получает только истощение дофамина.\n\nПоложи телефон экраном вниз на 2 минуты и сделай 5 глубоких вдохов. За это я уже начислил тебе <b>+20 очков</b>!",
    "🌬 <b>Техника «4-7-8» для быстрого сна:</b>\n1. Вдохни носом на 4 счета.\n2. Задержи дыхание на 7 счетов.\n3. Медленно выдохни ртом на 8 счетов.\n\nПовтори 3 раза — пульс замедлится сам. Держи <b>+20 очков</b> за заботу о себе!",
    "📝 <b>Выгрузка мыслей:</b> Если голова кипит от планов на завтра, мозг боится уснуть, чтобы ничего не забыть. Просто напиши мне сюда в чат всё, что тебя тревожит — я помогу разложить это по полочкам. Бонус за осознанность: <b>+20 очков</b>!"
)

def safe_edit(text, chat_id, message_id, reply_markup=None):
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception:
        pass

def get_rank(points):
    if points < 100:
        return "🦉 Ночная сова"
    elif points < 300:
        return "🕯 Искатель баланса"
    elif points < 600:
        return "🔋 Хранитель энергии"
    elif points < 1000:
        return "🧘 Мастер режима"
    else:
        return "👑 Повелитель времени"

def ask_ai_psychologist(user_text, user_data):
    system_prompt = (
        "Ты — теплый, мудрый и психологически поддерживающий ИИ-напарник в Telegram-боте для контроля сна. "
        f"У пользователя сейчас {user_data.get('points')} очков, серия {user_data.get('streak')} дней, время отбоя {user_data.get('bedtime')}. "
        "Отвечай коротко (3-5 предложений), по-дружески, с эмпатией и легким юмором. "
        "Никогда не ругай и не осуждай. Помогай мягко переключиться с тревожных мыслей или желания сидеть в телефоне на спокойный отдых."
    )
    full_prompt = f"{system_prompt}\n\nСообщение пользователя: {user_text}\nТвой ответ:"
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://pollinations.ai{encoded}"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and resp.text.strip():
            return resp.text.strip()
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        
    return "Я рядом и слышу тебя. Иногда мозгу просто нужно выговориться перед сном. Сделай глубокий вдох, отпусти дневную суету — завтра ты обязательно со всем справишься. 🌙"

def ensure_user(user_id):
    if user_id not in user_settings:
        rivals = list()
        base_scores = (150, 120, 90, 60, 40, 20)
        for name, score in zip(RIVAL_NAMES, base_scores):
            rivals.append({"name": name, "points": score, "streak": random.randint(1, 4)})
            
        user_settings.update({
            user_id: {
                "bedtime": "23:00",
                "prep_time": "22:30",
                "streak": 0,
                "points": 50,
                "active": False,
                "snooze_until": None,
                "deadline": None,
                "waiting_confirm": False,
                "duel_rival": None,
                "checkin_done": False,
                "rivals": rivals
            }
        })

def update_rivals(user_id):
    data = user_settings.get(user_id)
    for rival in data.get("rivals"):
        if random.random() < 0.80:
            rival.update({"points": rival.get("points") + 50, "streak": rival.get("streak") + 1})
        else:
            rival.update({"points": max(0, rival.get("points") - 40), "streak": 0})
    data.update({"checkin_done": False})

def get_dashboard_text(user_id):
    data = user_settings.get(user_id)
    rank = get_rank(data.get("points"))
    status = f"🟢 Активен (отбой в <b>{data.get('bedtime')}</b>)" if data.get("active") else f"⚪️ Не запущен (выбрано <b>{data.get('bedtime')}</b>)"
    duel_str = f"⚔️ Дуэль с <b>{data.get('duel_rival')}</b> (на кону 50 очк.)" if data.get("duel_rival") else "⚔️ Нет активной дуэли"
    
    return (
        "🌙 <b>ЦЕНТР УПРАВЛЕНИЯ СНОМ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏅 Ранг: <b>{rank}</b>\n"
        f"💎 Баланс: <b>{data.get('points')} очков</b> | 🔥 Серия: <b>{data.get('streak')} дн.</b>\n"
        f"⏰ Режим: {status}\n"
        f"{duel_str}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 <i>Можешь просто написать мне в чат, если тревожно, скучно или не спится — я отвечу как ИИ-психолог!</i>"
    )

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⏰ Настроить время", callback_data="menu_time"),
        types.InlineKeyboardButton("✅ Включить контроль", callback_data="save")
    )
    markup.add(
        types.InlineKeyboardButton("⚔️ Бросить вызов", callback_data="menu_duel"),
        types.InlineKeyboardButton("🏆 Рейтинг лиги", callback_data="leaderboard")
    )
    markup.add(
        types.InlineKeyboardButton("☀️ Утренний чек-ин", callback_data="morning_checkin"),
        types.InlineKeyboardButton("🆘 Хочу залипнуть", callback_data="anti_scroll")
    )
    return markup

def get_time_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=4)
    presets = ("22:30", "23:00", "23:30", "00:00")
    buttons = tuple(types.InlineKeyboardButton(t, callback_data=f"set_{t}") for t in presets)
    markup.add(*buttons)
    
    markup.add(
        types.InlineKeyboardButton("➖ 15 мин", callback_data="shift_-15"),
        types.InlineKeyboardButton("➕ 15 мин", callback_data="shift_15")
    )
    markup.add(types.InlineKeyboardButton("✅ Сохранить и запустить", callback_data="save"))
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    return markup

@bot.message_handler(commands=('start', 'menu'))
def cmd_start(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    bot.send_message(
        user_id,
        get_dashboard_text(user_id),
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def process_back(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    safe_edit(
        get_dashboard_text(user_id),
        user_id,
        call.message.message_id,
        get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "menu_time")
def process_menu_time(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    safe_edit(
        f"⏰ <b>Настройка времени отбоя (МСК)</b>\n\n"
        f"Сейчас выбрано: <b>{data.get('bedtime')}</b>\n"
        "Подбери комфортный час и нажми «Сохранить»:",
        user_id,
        call.message.message_id,
        get_time_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def process_preset(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    _, new_time = call.data.split("_")
    user_settings.get(user_id).update({"bedtime": new_time})
    safe_edit(
        f"⏰ <b>Настройка времени отбоя (МСК)</b>\n\n"
        f"Выбрано время: <b>{new_time}</b>\n"
        "Можешь подкорректировать по 15 минут или запустить контроль:",
        user_id,
        call.message.message_id,
        get_time_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shift_"))
def process_shift(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    _, min_str = call.data.split("_")
    minutes = int(min_str)
    current_str = user_settings.get(user_id).get("bedtime")
    
    dt = datetime.strptime(current_str, "%H:%M") + timedelta(minutes=minutes)
    new_time = dt.strftime("%H:%M")
    user_settings.get(user_id).update({"bedtime": new_time})
    
    safe_edit(
        f"⏰ <b>Настройка времени отбоя (МСК)</b>\n\n"
        f"Выбрано время: <b>{new_time}</b>\n"
        "Можешь подкорректировать по 15 минут или запустить контроль:",
        user_id,
        call.message.message_id,
        get_time_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "save")
def process_save(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    bedtime_str = data.get("bedtime")
    bed_dt = datetime.strptime(bedtime_str, "%H:%M")
    prep_dt = bed_dt - timedelta(minutes=30)
    
    data.update({
        "prep_time": prep_dt.strftime("%H:%M"),
        "active": True,
        "waiting_confirm": False,
        "snooze_until": None,
        "deadline": None
    })
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    
    safe_edit(
        f"✅ <b>Контракт со сном активирован!</b>\n\n"
        f"• В <b>{prep_dt.strftime('%H:%M')}</b> мягко напомню замедлиться.\n"
        f"• В <b>{bedtime_str}</b> проверю, в кровати ли ты.\n\n"
        "Если станет скучно или захочется поболтать перед сном — просто напиши мне любое сообщение!",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "menu_duel")
def process_menu_duel(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for idx, r in enumerate(data.get("rivals")):
        markup.add(types.InlineKeyboardButton(f"⚔️ {r.get('name')} ({r.get('points')} очк.)", callback_data=f"duel_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    
    safe_edit(
        "⚔️ <b>ДУЭЛЬ ЗА ОЧКИ РЕЖИМА</b>\n\n"
        "Выбери соперника на сегодняшний вечер:\n"
        "• Если ты ляжешь вовремя — заберешь <b>+50 очков</b> прямо из его копилки!\n"
        "• Если сорвешь отбой — твои <b>50 очков</b> уйдут ему.\n\n"
        "Кому бросим вызов?",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("duel_"))
def process_start_duel(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    _, idx_str = call.data.split("_")
    rival = data.get("rivals").__getitem__(int(idx_str))
    
    data.update({"duel_rival": rival.get("name")})
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    
    safe_edit(
        f"🔥 <b>Вызов принят!</b>\n\n"
        f"Сегодня вечером ты соревнуешься с <b>{rival.get('name')}</b>.\n"
        f"Участник уже получил уведомление и готовится лечь вовремя. Не дай ему забрать твои очки!",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "anti_scroll")
def process_anti_scroll(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    data.update({"points": data.get("points") + 20})
    
    tip = random.choice(ANTI_SCROLL_TIPS)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    
    safe_edit(
        f"🆘 <b>АНТИ-ЗАЛИПАНИЕ</b>\n\n{tip}",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "morning_checkin")
def process_morning_checkin(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    
    if data.get("checkin_done"):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
        safe_edit(
            "☀️ Ты уже проходил утренний чек-ин сегодня! Возвращайся завтра утром за новой порцией баллов.",
            user_id,
            call.message.message_id,
            markup
        )
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡️ Выспался отлично! (+25 очк.)", callback_data="mood_great"),
        types.InlineKeyboardButton("😐 Нормально, но можно лучше (+25 очк.)", callback_data="mood_ok"),
        types.InlineKeyboardButton("😴 Разбит, лег слишком поздно (+15 очк.)", callback_data="mood_bad")
    )
    safe_edit(
        "☀️ <b>УТРЕННИЙ ЧЕК-ИН</b>\n\nКак ты чувствуешь себя после пробуждения?",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("mood_"))
def process_mood(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    _, mood = call.data.split("_")
    
    bonus = 15 if mood == "bad" else 25
    data.update({
        "points": data.get("points") + bonus,
        "checkin_done": True
    })
    
    replies = {
        "great": "Вот что делает вовремя начатый сон! Энергия на максимуме, пусть день пройдет продуктивно! 🚀",
        "ok": "Отличное начало! Если сегодня ляжешь на 15 минут раньше, завтра утром почувствуешь еще больше легкости. 🌤",
        "bad": "Ничего страшного, у всех бывают тяжелые ночи. Не ругай себя — просто попей воды и сегодня вечером ляг пораньше. Я помогу! 💙"
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    
    safe_edit(
        f"✨ <b>Начислено +{bonus} очков энергии!</b>\n\n{replies.get(mood)}",
        user_id,
        call.message.message_id,
        markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def process_leaderboard(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    
    players = list()
    players.append({"name": "👉 ТЫ (Вы)", "points": data.get("points"), "streak": data.get("streak"), "is_me": True})
    for r in data.get("rivals"):
        players.append({"name": r.get("name"), "points": r.get("points"), "streak": r.get("streak"), "is_me": False})
    
    players.sort(key=lambda x: x.get("points"), reverse=True)
    medals = ("🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣")
    lines = list()
    lines.append("🏆 <b>ЛИГА ЗДОРОВОГО СНА (Топ-7):</b>\n")
    
    for idx, p in enumerate(players):
        medal = medals.__getitem__(idx) if idx < len(medals) else f"{idx+1}."
        if p.get("is_me"):
            lines.append(f"{medal} <b>{p.get('name')} — {p.get('points')} очк.</b> (серия {p.get('streak')} дн.)")
        else:
            lines.append(f"{medal} {p.get('name')} — {p.get('points')} очк. (серия {p.get('streak')} дн.)")
            
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚔️ Бросить вызов", callback_data="menu_duel"))
    markup.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu"))
    
    safe_edit(
        "\n".join(lines),
        user_id,
        call.message.message_id,
        markup
    )

def send_bedtime_question(user_id):
    data = user_settings.get(user_id)
    duel_text = f"\n⚔️ На кону победа в дуэли против <b>{data.get('duel_rival')}</b>!" if data.get("duel_rival") else ""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("😴 Я в кровати! (+50 очков)", callback_data="in_bed"),
        types.InlineKeyboardButton("⏳ Нужно еще 15 мин (-15 очков)", callback_data="snooze")
    )
    bot.send_message(
        user_id,
        f"⏰ <b>Время отбоя!</b>\n"
        f"Не поддавайся на уговоры мозга «посмотреть еще 5 минут».{duel_text}\n\n"
        f"Если не ляжешь в течение 45 минут, сгорит <b>100 очков</b> и серия из <b>{data.get('streak')} дн.</b>!",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "in_bed")
def process_in_bed(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    
    bonus = 50
    duel_msg = ""
    if data.get("duel_rival"):
        rival_name = data.get("duel_rival")
        bonus += 50
        duel_msg = f"\n⚔️ <b>Победа в дуэли!</b> Ты забрал +50 очков у <b>{rival_name}</b>!"
        for r in data.get("rivals"):
            if r.get("name") == rival_name:
                r.update({"points": max(0, r.get("points") - 50)})
                
    data.update({
        "streak": data.get("streak") + 1,
        "points": data.get("points") + bonus,
        "waiting_confirm": False,
        "snooze_until": None,
        "deadline": None,
        "duel_rival": None
    })
    
    safe_edit(
        f"🔥 <b>Отлично! +{bonus} очков!</b>{duel_msg}\n\n"
        f"• Твой баланс: <b>{data.get('points')} очков</b>\n"
        f"• Серия: <b>{data.get('streak')} дн. подряд</b>\n\n"
        "Отложи телефон экраном вниз. Спокойной ночи! 🌙",
        user_id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "snooze")
def process_snooze(call):
    user_id = call.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    
    snooze_dt = get_msk_now() + timedelta(minutes=15)
    data.update({
        "points": max(0, data.get("points") - 15),
        "snooze_until": snooze_dt.strftime("%H:%M")
    })
    
    safe_edit(
        f"⏳ <b>Отсрочка: -15 очков.</b> Осталось: <b>{data.get('points')}</b>.\n"
        "Завершай дела быстрее, напишу снова через 15 минут!",
        user_id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: True)
def handle_text_chat(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    data = user_settings.get(user_id)
    
    bot.send_chat_action(user_id, 'typing')
    reply = ask_ai_psychologist(message.text, data)
    bot.send_message(user_id, reply)

def time_checker():
    last_checked_minute = ""
    while True:
        now = get_msk_now()
        now_str = now.strftime("%H:%M")
        if now_str != last_checked_minute:
            last_checked_minute = now_str
            for user_id, data in list(user_settings.items()):
                if now_str == "23:45":
                    update_rivals(user_id)
                    
                if not data.get("active"):
                    continue
                
                if now_str == data.get("prep_time"):
                    bot.send_message(
                        user_id,
                        "🌙 <b>До сна осталось 30 минут!</b>\n"
                        "Приглуши свет и начни замедляться. Если в голове крутятся мысли или тревога — просто напиши мне сюда, мы всё обсудим.",
                        parse_mode="HTML"
                    )
                
                if now_str == data.get("bedtime"):
                    deadline_dt = now + timedelta(minutes=45)
                    data.update({
                        "waiting_confirm": True,
                        "deadline": deadline_dt.strftime("%H:%M")
                    })
                    send_bedtime_question(user_id)
                
                if now_str == data.get("snooze_until"):
                    data.update({"snooze_until": None})
                    send_bedtime_question(user_id)
                
                if data.get("waiting_confirm") and now_str == data.get("deadline"):
                    lost_streak = data.get("streak")
                    penalty = 100
                    duel_loss = ""
                    if data.get("duel_rival"):
                        rival_name = data.get("duel_rival")
                        penalty += 50
                        duel_loss = f"\n⚔️ Ты также проиграл дуэль: <b>{rival_name}</b> забрал 50 очков!"
                        for r in data.get("rivals"):
                            if r.get("name") == rival_name:
                                r.update({"points": r.get("points") + 50})
                                
                    new_points = max(0, data.get("points") - penalty)
                    data.update({
                        "waiting_confirm": False,
                        "deadline": None,
                        "snooze_until": None,
                        "duel_rival": None,
                        "streak": 0,
                        "points": new_points
                    })
                    
                    bot.send_message(
                        user_id,
                        f"💥 <b>Режим сорван! Сгорело {penalty} очков.</b>{duel_loss}\n"
                        f"Цепочка из <b>{lost_streak} дн.</b> обнулилась, текущий баланс: <b>{new_points} очков</b>.\n\n"
                        "Не ругай себя — просто закрой всё прямо сейчас и ложись спать, чтобы завтра начать с чистого листа.",
                        parse_mode="HTML"
                    )
        time.sleep(5)

threading.Thread(target=time_checker, daemon=True).start()
print("Бот с ИИ-психологом и дуэлями успешно запущен!")
bot.infinity_polling(skip_pending=True)
