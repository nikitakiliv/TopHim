import config
import sqlite3

bot = config.bot
# устанавливаем соединение с базой данных
conn = sqlite3.connect(config.database)
cursor = conn.cursor()

def view_user_statistics(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()

    # Получаем список всех пользователей
    cursor.execute('SELECT DISTINCT chat_id FROM user_answers')
    users = cursor.fetchall()

    if not users:
        bot.send_message(chat_id, "Нет данных о пользователях.")
        return

    for user in users:
        user_id = user[0]

        # Получаем имя пользователя (если есть)
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username = cursor.fetchone()
        if username:
            username = username[0]
        else:
            username = "Неизвестный пользователь"

        # Рассчитываем общий процент завершения для пользователя
        completion_percentage = calculate_completion_percentage(user_id)

        # Формируем сообщение с информацией о пользователе
        user_stats_message = f"Пользователь: {username}\n"
        user_stats_message += f"Общий процент завершения: {completion_percentage:.2f}%\n"

        # Получаем список всех тем, по которым пользователь отвечал
        cursor.execute('SELECT DISTINCT topic_id FROM user_answers WHERE chat_id = ?', (user_id,))
        topics = cursor.fetchall()

        if topics:
            user_stats_message += "Статистика по темам:\n"
            for topic in topics:
                topic_id = topic[0]
                topic_name = get_topic_name(topic_id)  # Функция, чтобы получить имя темы по её ID
                # Рассчитываем процент завершения для каждой темы
                topic_percentage = calculate_topic_percentage(user_id, topic_id)
                user_stats_message += f"{topic_name}: {topic_percentage:.2f}%\n"

        bot.send_message(chat_id, user_stats_message)

    conn.close()

def calculate_completion_percentage(chat_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_answers WHERE chat_id = ?', (chat_id,))
    answered_questions = cursor.fetchone()[0]
    conn.close()
    completion_percentage = (answered_questions / total_questions) * 100
    return completion_percentage

def calculate_topic_percentage(chat_id, topic_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions WHERE topic_id = ?', (topic_id,))
    total_questions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
    answered_questions = cursor.fetchone()[0]

    conn.close()

    topic_completion_percentage = (answered_questions / total_questions) * 100
    return topic_completion_percentage


# Функция для получения имени темы по её ID
def get_topic_name(topic_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT topic FROM topics WHERE id = ?', (topic_id,))
    topic_name = cursor.fetchone()[0]
    conn.close()
    return topic_name

