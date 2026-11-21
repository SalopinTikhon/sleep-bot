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
