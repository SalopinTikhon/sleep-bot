import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, now_msk
from database import init_db, get_user, update_field, find_rival
from ai_service import ask_psychologist
from scheduler import start_scheduler

bot = telebot.TeleBot(BOT_TOKEN)

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    kb.row(KeyboardButton("😴 Я лёг спать"), KeyboardButton("⚔️ Батл (20 монет)"))
    kb.row(KeyboardButton("⏰ Отбой 23:00"), KeyboardButton("⏰ Отбой 00:00"), KeyboardButton("📊 Профиль"))
    return kb

@bot.message_handler(commands=["start"])
def cmd_start(m):
    get_user(m.from_user.id, m.from_user.first_name)
    bot.send_message(m.chat.id, "🌙 Контроль сна запущен! Нижняя панель всегда закреплена.\nНапиши любой текст, чтобы пообщаться с ИИ-психологом.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "😴 Я лёг спать")
def btn_sleep(m):
    u = get_user(m.from_user.id)
    bonus = 15 if u[4] == "pinged" else 5
    update_field(u[0], "status", "asleep")
    update_field(u[0], "ping_ts", 0)
    update_field(u[0], "coins", u[2] + bonus)
    if u[7]:
        update_field(u[0], "coins", u[2] + bonus + u[8] * 2)
        update_field(u[7], "rival_id", 0)
        update_field(u[0], "rival_id", 0)
        try: bot.send_message(u[7], "😔 Соперник лёг вовремя и забрал банк батла!")
        except Exception: pass
    bot.send_message(m.chat.id, f"🛌 Доброй ночи! Начислено +{bonus} монет.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "⚔️ Батл (20 монет)")
def btn_battle(m):
    u = get_user(m.from_user.id)
    if u[7]: return bot.send_message(m.chat.id, "⚔️ Ты уже в активном батле!", reply_markup=main_kb())
    if u[2] < 20: return bot.send_message(m.chat.id, "❌ Недостаточно монет (нужно 20).", reply_markup=main_kb())
    rival = find_rival(u[0], 20)
    if not rival: return bot.send_message(m.chat.id, "🔎 Пока нет свободных соперников с 20 монетами. Позови друга!", reply_markup=main_kb())
    rid = rival[0]
    update_field(u[0], "coins", u[2] - 20); update_field(u[0], "rival_id", rid); update_field(u[0], "bet", 20)
    r_coins = get_user(rid)[2]
    update_field(rid, "coins", r_coins - 20); update_field(rid, "rival_id", u[0]); update_field(rid, "bet", 20)
    bot.send_message(m.chat.id, "⚔️ Соперник найден! Ставка 20 монет списана. Кто ляжет по будильнику — заберёт 40!", reply_markup=main_kb())
    try: bot.send_message(rid, "⚔️ Тебе брошен вызов на батл сна (ставка 20 монет)! Не проспи отбой!")
    except Exception: pass

@bot.message_handler(func=lambda m: m.text and m.text.startswith("⏰ Отбой "))
def btn_time(m):
    t = m.text.replace("⏰ Отбой ", "")
    update_field(m.from_user.id, "bedtime", t)
    update_field(m.from_user.id, "status", "awake")
    bot.send_message(m.chat.id, f"✅ Время отбоя установлено на {t} по МСК.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def btn_prof(m):
    u = get_user(m.from_user.id)
    battle_txt = "Активен ⚔️" if u[7] else "Нет"
    bot.send_message(m.chat.id, f"👤 {u[1]}\n💰 Монеты: {u[2]}\n⏰ Отбой (МСК): {u[3]}\n⚔️ Батл: {battle_txt}\n🕒 Сейчас МСК: {now_msk().strftime('%H:%M')}", reply_markup=main_kb())

@bot.message_handler(func=lambda m: True)
def ai_chat(m):
    bot.send_chat_action(m.chat.id, "typing")
    ans = ask_psychologist(m.text)
    bot.send_message(m.chat.id, f"🧠 {ans}", reply_markup=main_kb())

if __name__ == "__main__":
    init_db()
    start_scheduler(bot)
    bot.infinity_polling()
