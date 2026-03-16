from datetime import datetime, timedelta
from database import Database

async def daily_notification(bot):
    db = Database('schedule.db')
    users = db.get_users_with_notifications()
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    day_of_week = (datetime.now().weekday() + 1) % 7

    for user_id in users:
        class_name = db.get_user_class(user_id)
        if not class_name:
            continue
        schedule = db.get_schedule(class_name, day_of_week)
        homeworks = db.get_homeworks(class_name, tomorrow)
        text = f"🔔 Напоминание: расписание на завтра ({class_name})\n\n"
        if schedule:
            for lesson in schedule:
                text += f"{lesson[0]}. {lesson[1]}\n"
        else:
            text += "Расписания нет.\n"
        if homeworks:
            text += "\n📚 Домашние задания:\n"
            for subject, task in homeworks:
                text += f"{subject}: {task}\n"
        else:
            text += "\nДомашних заданий нет."
        try:
            await bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")
    db.close()