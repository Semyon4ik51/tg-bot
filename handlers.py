import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import (
    main_menu_keyboard, classes_keyboard, dates_keyboard,
    confirm_keyboard, cancel_keyboard, admin_menu_keyboard,
    subjects_keyboard
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
db = Database('schedule.db')

class Register(StatesGroup):
    choosing_class = State()

class AddHomework(StatesGroup):
    choosing_class = State()
    entering_date = State()
    entering_subject = State()
    entering_task = State()
    confirm = State()

class AddReplacement(StatesGroup):
    choosing_class = State()
    entering_date = State()
    entering_lesson = State()
    entering_info = State()
    confirm = State()

class ProposeScheduleChange(StatesGroup):
    waiting_for_new_schedule = State()

class AddHomeworkCollective(StatesGroup):
    choosing_subject = State()
    entering_task = State()

def is_admin(user_id: int) -> bool:
    role = db.get_user_role(user_id)
    return role == 'admin'

def get_weekday_name(day: int) -> str:
    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    return days[day]

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    if db.user_exists(user_id):
        await message.answer(
            f"С возвращением, {full_name}!",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer("👋 Добро пожаловать! Для начала работы выберите ваш класс.")
        classes = ['5', '6а', '6б', '7а', '8', '9', '10', '11']
        await message.answer("Выберите класс:", reply_markup=classes_keyboard(classes))
        await state.set_state(Register.choosing_class)

@router.callback_query(Register.choosing_class, F.data.startswith('class_'))
async def register_class_chosen(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace('class_', '')
    user_id = callback.from_user.id
    full_name = callback.from_user.full_name

    db.add_user(user_id, full_name, class_name, role='student')
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Регистрация завершена! Ваш класс: {class_name}",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
    await state.clear()

@router.callback_query(F.data == 'cancel')
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.message(F.text == '📅 Расписание на сегодня')
async def today_schedule(message: Message):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    if not class_name:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    day = datetime.now().weekday()
    schedule = db.get_schedule(class_name, day)

    if not schedule:
        await message.answer("📭 На сегодня расписания нет.")
        return

    text = f"📅 *Расписание на {get_weekday_name(day)} ({class_name}):*\n\n"
    for lesson in schedule:
        text += f"{lesson[0]}. {lesson[1]}\n"

    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '📅 Расписание на завтра')
async def tomorrow_schedule(message: Message):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    if not class_name:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    day = (datetime.now().weekday() + 1) % 7
    schedule = db.get_schedule(class_name, day)

    if not schedule:
        await message.answer("📭 На завтра расписания нет.")
        return

    text = f"📅 *Расписание на {get_weekday_name(day)} ({class_name}):*\n\n"
    for lesson in schedule:
        text += f"{lesson[0]}. {lesson[1]}\n"

    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '📚 Домашнее задание')
async def homework_menu(message: Message):
    await message.answer("Выберите дату:", reply_markup=dates_keyboard())

@router.callback_query(F.data.startswith('date_'))
async def homework_date_chosen(callback: CallbackQuery):
    choice = callback.data
    user_id = callback.from_user.id
    class_name = db.get_user_class(user_id)

    if not class_name:
        await callback.message.answer("❌ Сначала зарегистрируйтесь через /start")
        await callback.answer()
        return

    today = datetime.now().date()
    if choice == 'date_today':
        target_date = today
    elif choice == 'date_tomorrow':
        target_date = today + timedelta(days=1)
    elif choice == 'date_other':
        await callback.message.answer("⏳ Ввод произвольной даты пока не реализован.")
        await callback.answer()
        return
    else:
        await callback.answer()
        return

    date_str = target_date.strftime('%Y-%m-%d')
    homeworks = db.get_homeworks(class_name, date_str)

    if not homeworks:
        await callback.message.answer(f"📭 На {target_date.strftime('%d.%m.%Y')} домашних заданий нет.")
    else:
        text = f"📚 *Домашнее задание на {target_date.strftime('%d.%m.%Y')} ({class_name}):*\n\n"
        for subject, task in homeworks:
            text += f"*{subject}:* {task}\n"
        await callback.message.answer(text, parse_mode='Markdown')

    await callback.answer()

@router.message(F.text == '⚠️ Замены')
async def replacements_today(message: Message):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    if not class_name:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    today = datetime.now().date().strftime('%Y-%m-%d')
    replacements = db.get_replacements(class_name, today)

    if not replacements:
        await message.answer("✅ На сегодня замен нет.")
        return

    text = f"⚠️ *Замены на сегодня ({class_name}):*\n\n"
    for lesson_num, info in replacements:
        text += f"*{lesson_num} урок:* {info}\n"
    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '🗓 Каникулы')
async def holidays_info(message: Message):
    holidays = db.get_holidays()
    if not holidays:
        await message.answer("Информация о каникулах пока не добавлена.")
        return

    text = "🗓 *Каникулы и праздники:*\n\n"
    for start, end, name in holidays:
        text += f"*{name}:* {start} – {end}\n"
    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '⚙️ Админ-панель')
async def admin_panel(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ У вас нет прав для доступа к админ-панели.")
        return
    await message.answer("Админ-панель:", reply_markup=admin_menu_keyboard())

@router.message(F.text == '➕ Добавить ДЗ')
async def add_homework_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ Только администраторы могут добавлять ДЗ.")
        return

    classes = ['5', '6а', '6б', '7а', '8', '9', '10', '11']
    await message.answer("Выберите класс:", reply_markup=classes_keyboard(classes))
    await state.set_state(AddHomework.choosing_class)

@router.callback_query(AddHomework.choosing_class, F.data.startswith('class_'))
async def add_homework_class_chosen(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace('class_', '')
    await state.update_data(class_name=class_name)
    await callback.message.delete()
    await callback.message.answer(
        "Введите дату в формате ГГГГ-ММ-ДД (например, 2026-03-20):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddHomework.entering_date)
    await callback.answer()

@router.message(AddHomework.entering_date, F.text)
async def add_homework_date_entered(message: Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату ещё раз (ГГГГ-ММ-ДД):")
        return

    await state.update_data(date=date_str)
    await message.answer("Введите предмет:")
    await state.set_state(AddHomework.entering_subject)

@router.message(AddHomework.entering_subject, F.text)
async def add_homework_subject_entered(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await message.answer("Введите текст домашнего задания:")
    await state.set_state(AddHomework.entering_task)

@router.message(AddHomework.entering_task, F.text)
async def add_homework_task_entered(message: Message, state: FSMContext):
    await state.update_data(task=message.text.strip())
    data = await state.get_data()
    confirmation_text = (
        f"Проверьте данные:\n"
        f"Класс: {data['class_name']}\n"
        f"Дата: {data['date']}\n"
        f"Предмет: {data['subject']}\n"
        f"Задание: {data['task']}\n\n"
        f"Всё верно?"
    )
    await message.answer(confirmation_text, reply_markup=confirm_keyboard())
    await state.set_state(AddHomework.confirm)

@router.callback_query(AddHomework.confirm, F.data == 'confirm_yes')
async def add_homework_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    db.add_homework(
        class_name=data['class_name'],
        date=data['date'],
        subject=data['subject'],
        task=data['task']
    )
    await callback.message.delete()
    await callback.message.answer(
        "✅ Домашнее задание успешно добавлено!",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(AddHomework.confirm, F.data == 'confirm_no')
async def add_homework_confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Добавление отменено.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.message(F.text == '✏️ Добавить замену')
async def add_replacement_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ Только администраторы могут добавлять замены.")
        return
    classes = ['5', '6а', '6б', '7а', '8', '9', '10', '11']
    await message.answer("Выберите класс:", reply_markup=classes_keyboard(classes))
    await state.set_state(AddReplacement.choosing_class)

@router.callback_query(AddReplacement.choosing_class, F.data.startswith('class_'))
async def add_replacement_class_chosen(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace('class_', '')
    await state.update_data(class_name=class_name)
    await callback.message.delete()
    await callback.message.answer(
        "Введите дату замены в формате ГГГГ-ММ-ДД (например, 2026-03-20):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddReplacement.entering_date)
    await callback.answer()

@router.message(AddReplacement.entering_date, F.text)
async def add_replacement_date_entered(message: Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату ещё раз (ГГГГ-ММ-ДД):")
        return
    await state.update_data(date=date_str)
    await message.answer("Введите номер урока, которого касается замена:")
    await state.set_state(AddReplacement.entering_lesson)

@router.message(AddReplacement.entering_lesson, F.text)
async def add_replacement_lesson_entered(message: Message, state: FSMContext):
    try:
        lesson_num = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число (номер урока):")
        return
    await state.update_data(lesson_number=lesson_num)
    await message.answer("Введите информацию о замене (например, 'вместо истории будет математика, каб. 12'):")
    await state.set_state(AddReplacement.entering_info)

@router.message(AddReplacement.entering_info, F.text)
async def add_replacement_info_entered(message: Message, state: FSMContext):
    await state.update_data(new_info=message.text.strip())
    data = await state.get_data()
    confirmation_text = (
        f"Проверьте данные:\n"
        f"Класс: {data['class_name']}\n"
        f"Дата: {data['date']}\n"
        f"Урок: {data['lesson_number']}\n"
        f"Замена: {data['new_info']}\n\n"
        f"Всё верно?"
    )
    await message.answer(confirmation_text, reply_markup=confirm_keyboard())
    await state.set_state(AddReplacement.confirm)

@router.callback_query(AddReplacement.confirm, F.data == 'confirm_yes')
async def add_replacement_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    db.add_replacement(
        class_name=data['class_name'],
        date=data['date'],
        lesson_number=data['lesson_number'],
        new_info=data['new_info']
    )
    users = db.get_users_by_class(data['class_name'])
    replacement_text = (
        f"⚠️ *Срочная замена для {data['class_name']}*\n"
        f"Дата: {data['date']}\n"
        f"Урок {data['lesson_number']}: {data['new_info']}"
    )
    for user_id in users:
        try:
            await callback.bot.send_message(chat_id=user_id, text=replacement_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Не удалось отправить замену пользователю {user_id}: {e}")
    await callback.message.delete()
    await callback.message.answer(
        "✅ Замена успешно добавлена и разослана!",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(AddReplacement.confirm, F.data == 'confirm_no')
async def add_replacement_confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Добавление отменено.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.message(F.text == "✏️ Предложить изменение расписания")
async def propose_schedule_change_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    if not class_name:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    tomorrow_day = (datetime.now().weekday() + 1) % 7
    schedule = db.get_schedule(class_name, tomorrow_day)

    if schedule:
        text = f"📅 Текущее расписание на завтра ({class_name}):\n"
        for lesson in schedule:
            text += f"{lesson[0]}. {lesson[1]}\n"
        text += "\nОтправьте исправленное расписание (каждый урок с новой строки):"
        await message.answer(text)
    else:
        await message.answer("📭 На завтра расписания нет. Отправьте новое расписание текстом (каждый урок с новой строки).")

    await state.set_state(ProposeScheduleChange.waiting_for_new_schedule)

@router.message(ProposeScheduleChange.waiting_for_new_schedule, F.text)
async def propose_schedule_change_receive(message: Message, state: FSMContext):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    new_schedule_text = message.text

    users = db.get_users_by_class(class_name)
    from_user = message.from_user.full_name or f"Пользователь {user_id}"
    broadcast_text = f"✏️ Предложение изменения расписания от {from_user}:\n\n{new_schedule_text}"

    sent_count = 0
    for uid in users:
        try:
            await message.bot.send_message(chat_id=uid, text=broadcast_text)
            sent_count += 1
        except Exception as e:
            print(f"Не удалось отправить пользователю {uid}: {e}")

    await message.answer(f"✅ Ваше предложение отправлено {sent_count} ученикам класса {class_name}.")
    await state.clear()

@router.message(F.text == "📝 Добавить ДЗ (для всех)")
async def add_homework_collective_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    if not class_name:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return

    subjects = db.get_subjects_for_class(class_name)
    if not subjects:
        await message.answer("❌ Для вашего класса пока нет предметов в расписании.")
        return

    await message.answer("Выберите предмет:", reply_markup=subjects_keyboard(subjects))
    await state.set_state(AddHomeworkCollective.choosing_subject)

@router.callback_query(AddHomeworkCollective.choosing_subject, F.data.startswith('subj_'))
async def add_homework_collective_subject_chosen(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.replace('subj_', '')
    await state.update_data(subject=subject)
    await callback.message.delete()
    await callback.message.answer(f"Введите домашнее задание по предмету '{subject}':")
    await state.set_state(AddHomeworkCollective.entering_task)
    await callback.answer()

@router.message(AddHomeworkCollective.entering_task, F.text)
async def add_homework_collective_task_entered(message: Message, state: FSMContext):
    user_id = message.from_user.id
    class_name = db.get_user_class(user_id)
    task = message.text
    data = await state.get_data()
    subject = data['subject']

    users = db.get_users_by_class(class_name)
    from_user = message.from_user.full_name or f"Пользователь {user_id}"
    broadcast_text = f"📚 Новое домашнее задание от {from_user}\nПредмет: {subject}\nЗадание: {task}"

    sent_count = 0
    for uid in users:
        try:
            await message.bot.send_message(chat_id=uid, text=broadcast_text)
            sent_count += 1
        except Exception as e:
            print(f"Не удалось отправить пользователю {uid}: {e}")

    await message.answer(f"✅ Домашнее задание отправлено {sent_count} ученикам класса {class_name}.")
    await state.clear()

@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "Я не понимаю эту команду. Воспользуйтесь кнопками меню.",
        reply_markup=main_menu_keyboard()
    )