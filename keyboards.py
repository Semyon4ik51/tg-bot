from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    buttons = [
        [KeyboardButton(text="📅 Расписание на сегодня")],
        [KeyboardButton(text="📅 Расписание на завтра")],
        [KeyboardButton(text="📚 Домашнее задание")],
        [KeyboardButton(text="⚠️ Замены"), KeyboardButton(text="🗓 Каникулы")],
        [KeyboardButton(text="✏️ Предложить изменение расписания")],
        [KeyboardButton(text="📝 Добавить ДЗ (для всех)")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def classes_keyboard(classes_list):
    buttons = []
    row = []
    for i, class_name in enumerate(classes_list, 1):
        row.append(InlineKeyboardButton(text=class_name, callback_data=f"class_{class_name}"))
        if i % 3 == 0 or i == len(classes_list):
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def dates_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Сегодня", callback_data="date_today")],
        [InlineKeyboardButton(text="Завтра", callback_data="date_tomorrow")],
        [InlineKeyboardButton(text="Другая дата", callback_data="date_other")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_keyboard():
    buttons = [[InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_keyboard():
    buttons = [[InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_menu_keyboard():
    buttons = [
        [KeyboardButton(text="➕ Добавить ДЗ")],
        [KeyboardButton(text="✏️ Добавить замену")],
        [KeyboardButton(text="📅 Добавить каникулы")],
        [KeyboardButton(text="🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def subjects_keyboard(subjects):
    """Инлайн-клавиатура для выбора предмета."""
    buttons = []
    for subject in subjects:
        buttons.append([InlineKeyboardButton(text=subject, callback_data=f"subj_{subject}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)