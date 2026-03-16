import sqlite3

class Database:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        # Для корректной работы с русскими символами
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                class_name TEXT,
                role TEXT DEFAULT 'student',
                notifications BOOLEAN DEFAULT 1
            )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            day INTEGER,
            lesson_number INTEGER,
            subject TEXT
        )
    ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS homeworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT,
                date TEXT,
                subject TEXT,
                task TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS replacements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT,
                date TEXT,
                lesson_number INTEGER,
                new_info TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT,
                end_date TEXT,
                name TEXT
            )
        ''')
        self.conn.commit()


    def user_exists(self, user_id):
        result = self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return bool(result.fetchone())

    def add_user(self, user_id, full_name, class_name, role='student'):
        self.cursor.execute('''
            INSERT INTO users (user_id, full_name, class_name, role) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, class_name, role))
        self.conn.commit()

    def get_user_class(self, user_id):
        result = self.cursor.execute('SELECT class_name FROM users WHERE user_id = ?', (user_id,))
        row = result.fetchone()
        return row[0] if row else None

    def get_user_role(self, user_id):
        result = self.cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        row = result.fetchone()
        return row[0] if row else None

    def set_notifications(self, user_id, enabled):
        self.cursor.execute('UPDATE users SET notifications = ? WHERE user_id = ?', (int(enabled), user_id))
        self.conn.commit()

    def get_users_with_notifications(self):
        result = self.cursor.execute('SELECT user_id FROM users WHERE notifications = 1')
        return [row[0] for row in result.fetchall()]


    def get_schedule(self, class_name, day):
        result = self.cursor.execute('''
            SELECT lesson_number, subject FROM schedule 
            WHERE class_name = ? AND day = ? 
            ORDER BY lesson_number
        ''', (class_name, day))
        return result.fetchall()  

    def add_lesson(self, class_name, day, lesson_number, subject):
        self.cursor.execute('''
            INSERT INTO schedule (class_name, day, lesson_number, subject)
            VALUES (?, ?, ?, ?)
        ''', (class_name, day, lesson_number, subject))
        self.conn.commit()


    def get_homeworks(self, class_name, date):
        result = self.cursor.execute('''
            SELECT subject, task FROM homeworks 
            WHERE class_name = ? AND date = ?
        ''', (class_name, date))
        return result.fetchall()

    def add_homework(self, class_name, date, subject, task):
        self.cursor.execute('''
            INSERT INTO homeworks (class_name, date, subject, task)
            VALUES (?, ?, ?, ?)
        ''', (class_name, date, subject, task))
        self.conn.commit()


    def add_replacement(self, class_name, date, lesson_number, new_info):
        self.cursor.execute('''
            INSERT INTO replacements (class_name, date, lesson_number, new_info)
            VALUES (?, ?, ?, ?)
        ''', (class_name, date, lesson_number, new_info))
        self.conn.commit()

    def get_replacements(self, class_name, date):
        result = self.cursor.execute('''
            SELECT lesson_number, new_info FROM replacements 
            WHERE class_name = ? AND date = ?
        ''', (class_name, date))
        return result.fetchall()


    def get_holidays(self):
        result = self.cursor.execute('''
            SELECT start_date, end_date, name FROM holidays 
            ORDER BY start_date
        ''')
        return result.fetchall()

    def add_holiday(self, start_date, end_date, name):
        self.cursor.execute('''
            INSERT INTO holidays (start_date, end_date, name)
            VALUES (?, ?, ?)
        ''', (start_date, end_date, name))
        self.conn.commit()

    def get_users_by_class(self, class_name):
        result = self.cursor.execute('SELECT user_id FROM users WHERE class_name = ?', (class_name,))
        return [row[0] for row in result.fetchall()]

    def get_subjects_for_class(self, class_name):
        result = self.cursor.execute('SELECT DISTINCT subject FROM schedule WHERE class_name = ?', (class_name,))
        return [row[0] for row in result.fetchall()]


    def close(self):
        self.conn.close()