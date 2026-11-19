import time
import threading
from datetime import datetime, timedelta, timezone
import telebot
from telebot import types

# Вставьте сюда ваш токен от @BotFather
TOKEN = "9208055776:AAE5l3eGpfIBkSoF6yk1IMCIhagmw8hICEQ"
bot = telebot.TeleBot(TOKEN)

# Московский часовой пояс (UTC+3)
MSK = timezone(timedelta(hours=3))

def get_msk_now():
    return datetime.now(MSK)

user_settings = {}

def get_time_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=4)
    presets = ["22:30", "23:00", "23:30", "00:00"]
    buttons = [types.InlineKeyboardButton(t, callback_data=f"set_{t}") for t in presets]
    markup.add(*buttons)
    
    markup.add(
        types.InlineKeyboardButton("➖ 15 мин", callback_data="shift_-15"),
        types.InlineKeyboardButton("➕ 15 мин", callback_data="shift_15")
    )
    markup.add(types.InlineKeyboardButton("✅ Сохранить и запустить", callback_data="save"))
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": False, "snooze_until": None}
    bot.send_message(
        user_id,
        "Привет! Я помогу тебе ложиться спать вовремя.\n\n"
        "Текущее время отбоя (МСК): <b>23:00</b>\n"
        "Выбери удобное время кнопками ниже:",
        reply_markup=get_time_keyboard(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def process_preset(call):
    user_id = call.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": False, "snooze_until": None}
    new_time = call.data.split("_")[1]
    user_settings[user_id]["bedtime"] = new_time
    bot.edit_message_text(
        f"Выбрано время отбоя: <b>{new_time}</b>\n"
        "Можешь подкорректировать или нажать «Сохранить»:",
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=get_time_keyboard(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shift_"))
def process_shift(call):
    user_id = call.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": False, "snooze_until": None}
    minutes = int(call.data.split("_")[1])
    current_str = user_settings[user_id]["bedtime"]
    
    dt = datetime.strptime(current_str, "%H:%M") + timedelta(minutes=minutes)
    new_time = dt.strftime("%H:%M")
    user_settings[user_id]["bedtime"] = new_time
    
    bot.edit_message_text(
        f"Выбрано время отбоя: <b>{new_time}</b>\n"
        "Можешь подкорректировать или нажать «Сохранить»:",
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=get_time_keyboard(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "save")
def process_save(call):
    user_id = call.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": False, "snooze_until": None}
    bedtime_str = user_settings[user_id]["bedtime"]
    bed_dt = datetime.strptime(bedtime_str, "%H:%M")
    prep_dt = bed_dt - timedelta(minutes=30)
    
    user_settings[user_id]["prep_time"] = prep_dt.strftime("%H:%M")
    user_settings[user_id]["active"] = True
    
    bot.edit_message_text(
        f"✅ <b>Режим установлен!</b>\n\n"
        f"• Напомню о подготовке в <b>{prep_dt.strftime('%H:%M')}</b>\n"
        f"• Проверю отбой ровно в <b>{bedtime_str}</b>\n\n"
        "Чтобы изменить время, снова напиши /start",
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode="HTML"
    )

def send_bedtime_question(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("😴 Я в кровати!", callback_data="in_bed"),
        types.InlineKeyboardButton("⏳ Нужно еще 15 мин", callback_data="snooze")
    )
    bot.send_message(
        user_id,
        "⏰ <b>Время отбоя!</b> Ты уже в кровати?",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "in_bed")
def process_in_bed(call):
    user_id = call.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": True, "snooze_until": None}
    user_settings[user_id]["streak"] += 1
    streak = user_settings[user_id]["streak"]
    bot.edit_message_text(
        f"🔥 <b>Отлично! Спокойной ночи!</b>\n"
        f"Твоя серия вовремя начатого сна: <b>{streak} дн. подряд</b>.",
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "snooze")
def process_snooze(call):
    user_id = call.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"bedtime": "23:00", "streak": 0, "active": True, "snooze_until": None}
    snooze_dt = get_msk_now() + timedelta(minutes=15)
    user_settings[user_id]["snooze_until"] = snooze_dt.strftime("%H:%M")
    bot.edit_message_text(
        "Хорошо, даю 15 минут. Напишу снова! ⏳",
        chat_id=user_id,
        message_id=call.message.message_id
    )

def time_checker():
    last_checked_minute = ""
    while True:
        now_str = get_msk_now().strftime("%H:%M")
        if now_str != last_checked_minute:
            last_checked_minute = now_str
            for user_id, data in list(user_settings.items()):
                if not data.get("active"):
                    continue
                if now_str == data.get("prep_time"):
                    bot.send_message(
                        user_id,
                        "🌙 <b>До сна осталось 30 минут!</b>\n"
                        "Пора завершать дела, проветрить комнату и отложить телефон.",
                        parse_mode="HTML"
                    )
                if now_str == data.get("bedtime"):
                    send_bedtime_question(user_id)
                if now_str == data.get("snooze_until"):
                    data["snooze_until"] = None
                    send_bedtime_question(user_id)
        time.sleep(5)

threading.Thread(target=time_checker, daemon=True).start()
print("Бот успешно запущен в облаке!")
bot.infinity_polling()
