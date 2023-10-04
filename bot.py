import config
import logging
import admin
import os.path
import sqlite3
import random
import ReworkTopic
import AddQuestionsToTopic
import telebot
from itertools import *
import telebot.types as types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)

bot = config.bot
admin_chat_id = 1111111111

conn = sqlite3.connect(config.database)
cursor = conn.cursor()


# функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name
    user = user_db_matching(username, user_id)
    if user == True:
        greeting = f"Привет {first_name}, добро пожаловать в бота! Пожалуйста, выберите тему для продолжения:"
        add_user_to_db(user_id, username, first_name)
        reply_markup = create_inline_buttons_from_db()
        bot.send_message(chat_id=user_id, text=greeting, reply_markup=reply_markup)
    else:
        bot.send_message(chat_id = user_id, text = "Вы не были добавлены в white лист, для получение доступа к боту. Напишите преподователю для решения этой проблемы.")

def user_db_matching(username, user_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT username, user_id FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for user in users:
        db_username, db_user_id = user
        if db_user_id is not None and db_user_id == user_id:
            return True
        elif db_username == username:
            return True
    
    return False

def add_user_to_db(user_id, username, first_name):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    # Проверка, существует ли запись с заданным username
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Если user_id или first_name пустые, обновляем запись
        if user_id or first_name:
            update_query = "UPDATE users SET user_id = ?, first_name = ? WHERE username = ?"
            cursor.execute(update_query, (user_id, first_name, username))
        else:
            update_query = "UPDATE users SET username = ? WHERE user_id = ?, first_name = ?"
            cursor.execute(update_query, (username, user_id, first_name))
    else:
        # Вставка новой записи
        insert_query = "INSERT INTO users (username, user_id, first_name) VALUES (?, ?, ?)"
        cursor.execute(insert_query, (username, user_id, first_name))
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    cursor.close()
    conn.close()

@bot.message_handler(commands=['topic'])
def choose_ur_topic(message):
    user_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name
    user = user_db_matching(None, message.chat.id)
    if user == True:
        topic_message = "Выбери тему:"
        add_user_to_db(user_id, username, first_name)
        bot.send_message(message.from_user.id, topic_message, reply_markup=create_inline_buttons_from_db())
    else:
        bot.send_message(message.chat.id, text = "Вы не были добавлены в white лист, для получение доступа к боту. Напишите преподователю для решения этой проблемы.")

def topic_selection(chat_id):
    user = user_db_matching(None, chat_id)
    if user == True:
        topic_message = "Выбери тему:"
        bot.send_message(chat_id, topic_message, reply_markup=create_inline_buttons_from_db())
    else:
        bot.send_message(chat_id, text = "Вы не были добавлены в white лист, для получение доступа к боту. Напишите преподователю для решения этой проблемы.")

def create_inline_buttons_from_db():
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT id, topic FROM topics')
    data = cursor.fetchall()
    button_dict = {}
    keyboard = []
    for item in data:
        id = item[0]
        topic = item[1]
        if topic not in button_dict.keys():
            button = InlineKeyboardButton(text=topic, callback_data=id)
            keyboard.append([button])
            button_dict[id] = topic
    button_stats = InlineKeyboardButton(text="Показать статистику по всем тестам", callback_data="show_stats")
    reply_markup = InlineKeyboardMarkup(keyboard, row_width=2).add(button_stats)
    cursor.close()
    conn.close()

    return reply_markup


@bot.callback_query_handler(func=lambda call: True)
def wait_topic(call):
    user = user_db_matching(call.message.chat.username, call.message.chat.id)
    if user == True:
        conn = sqlite3.connect(config.database)
        cursor = conn.cursor()
        if call.data.endswith("_add"):
            call.data = call.data.replace("_add", "")
            cursor = conn.cursor()
            cursor.execute('SELECT topic FROM topics WHERE id=?', (call.data,))
            row = cursor.fetchone()
            if not row:
                return
            cursor.close()
            conn.close()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            AddQuestionsToTopic.choose_question(call.message.chat.id, call.data)
        elif call.data.endswith("_rework"):
            call.data = call.data.replace("_rework", "")
            cursor.execute('SELECT topic FROM topics WHERE id=?', (call.data,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return
            cursor.close()
            conn.close()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            ReworkTopic.choose_question(call.message.chat.id, call.data)
        elif call.data == "show_stats":
                send_completion_percentage(call.message.chat.id)
                return
        else:
            cursor.execute('SELECT topic FROM topics WHERE id=?', (call.data,))
            row = cursor.fetchone()
            if not row:
                return
            # Check if user has answered questions in this topic
            user_chat_id = call.message.chat.id
            topic_id = call.data
            cursor.execute('SELECT MAX(question_number) FROM user_answers WHERE chat_id=? AND topic_id=?', (user_chat_id, topic_id))
            last_question_number = cursor.fetchone()[0]
            if last_question_number is None:
                question_number = 1
            else:
                question_number = last_question_number + 1
            bot.delete_message(call.message.chat.id, call.message.message_id)
            message = bot.send_message(call.message.chat.id, "Начинаем тест!")
            cursor.close()
            conn.close()
            ask_question(call.message.chat.id, call.data)
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text = "Вы не были добавлены в white лист, для получение доступа к боту. Напишите преподователю для решения этой проблемы.")

def calculate_completion_percentage(chat_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_answers WHERE chat_id = ?', (chat_id,))
    answered_questions = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    completion_percentage = (answered_questions / total_questions) * 100
    return completion_percentage

def send_completion_percentage(chat_id):
    completion_percentage = calculate_completion_percentage(chat_id)
    message = f"Выполнено: {completion_percentage:.2f}%"
    bot.send_message(chat_id, message)

def ask_question(chat_id, topic_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT question_number, question, picture, weight FROM questions WHERE topic_id = ?', (topic_id,))
    all_questions = cursor.fetchall()
    cursor.execute('SELECT question_number FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
    answered_questions = set(row[0] for row in cursor.fetchall())
    if len(answered_questions) == len(all_questions):
        cursor.execute('DELETE FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
        conn.commit()
        bot.send_message(chat_id, "Ваши ответы в этой теме были сброшены. Начнем тест заново.")
    available_questions = [question for question in all_questions if question[0] not in answered_questions]
    question_texts = [question[1] for question in available_questions]
    question_weights = [question[3] for question in available_questions]
    selected_question_text = random.choices(question_texts, weights=question_weights)[0]
    selected_question = next(question for question in available_questions if question[1] == selected_question_text)
    question_number, question_text, picture = selected_question[:3]
    formatted_question = f"{question_text}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("❓ Вернуться к выбору темы")
    btn2 = types.KeyboardButton("Показать статистику по теме")
    markup.add(btn1).add(btn2)
    msg = bot.send_message(chat_id, formatted_question, reply_markup=markup)
    if picture:
        if os.path.isfile(os.path.join(config.FilePath, picture)):
            with open(os.path.join(config.FilePath, picture), 'rb') as f:
                bot.send_photo(chat_id, f)
        else:
            bot.send_message(admin_chat_id, f"Picture file {picture} not found")
    cursor.close()
    conn.close()
    bot.register_next_step_handler(msg, lambda message: check_answer(chat_id, topic_id, question_number, message.text))

def check_answer(chat_id, topic_id, question_number, answer):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT answer, secondAnswer, reaction FROM questions WHERE topic_id = ? AND question_number = ?', (topic_id, question_number))
    correct_answers = cursor.fetchone()
    correct_answer = correct_answers[0]
    second_answer = correct_answers[1]
    reaction = correct_answers[2]
    if answer == "/topic" or answer == "❓ Вернуться к выбору темы":
        conn.commit()
        cursor.close()
        conn.close()
        topic_selection(chat_id)
    elif answer == "Показать статистику по теме":
        conn.commit()
        cursor.close()
        conn.close()
        message = send_topic_percentage(chat_id, topic_id)
        message_return = bot.send_message(chat_id, message)
        bot.register_next_step_handler(message_return, lambda message: check_answer(chat_id, topic_id, question_number, message.text))
    elif reaction == 1:
        answer = ReactionChange(answer, correct_answer)
        if answer == correct_answer:
            cursor.execute('INSERT OR REPLACE INTO user_answers (chat_id, topic_id, question_number, user_answer) VALUES (?, ?, ?, ?)',
                        (chat_id, topic_id, question_number, answer))
            bot.send_message(chat_id, 'Верно!')
            cursor.execute('SELECT COUNT(*) FROM questions WHERE topic_id = ?', (topic_id,))
            total_question_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(DISTINCT question_number) FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
            answered_question_count = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            if answered_question_count == total_question_count:
                bot.send_message(chat_id, 'Поздравляю! Вы ответили на все вопросы по этой теме.')
                topic_selection(chat_id)
            else:
                ask_question(chat_id, topic_id)
        else:
            msg = bot.send_message(chat_id, 'Неверно. Пожалуйста, попробуй ещё раз.')
            cursor.close()
            conn.close()
            ask_question(chat_id, topic_id)
    elif answer == correct_answer or answer == second_answer:
        cursor.execute('INSERT OR REPLACE INTO user_answers (chat_id, topic_id, question_number, user_answer) VALUES (?, ?, ?, ?)',
                    (chat_id, topic_id, question_number, answer))
        bot.send_message(chat_id, 'Верно!')
        cursor.execute('SELECT COUNT(*) FROM questions WHERE topic_id = ?', (topic_id,))
        total_question_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT question_number) FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
        answered_question_count = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        if answered_question_count == total_question_count:
            bot.send_message(chat_id, 'Поздравляю! Вы ответили на все вопросы по этой теме.')
            topic_selection(chat_id)
        else:
            ask_question(chat_id, topic_id)
    else:
        msg = bot.send_message(chat_id, 'Неверно.')
        conn.commit()
        cursor.close()
        conn.close()
        ask_question(chat_id, topic_id)

def calculate_topic_percentage(chat_id, topic_id):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions WHERE topic_id = ?', (topic_id,))
    total_questions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_answers WHERE chat_id = ? AND topic_id = ?', (chat_id, topic_id))
    answered_questions = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    topic_completion_percentage = (answered_questions / total_questions) * 100
    return topic_completion_percentage

def send_topic_percentage(chat_id, topic_id):
    completion_percentage = calculate_topic_percentage(chat_id, topic_id)
    message = f"Выполнено: {completion_percentage:.2f}%"
    return message

def ReactionChange(answer, correct_answer):
    sp1, sp2 = correct_answer.split('=')
    sp1 = sp1.replace('+', ' ').split()
    sp2 = sp2.replace('+', ' ').split()
    a, b = answer.split('=')
    a = a.replace('+', ' ').split()
    b = b.replace('+', ' ').split()
    if sorted(a) == sorted(sp1):
        if sorted(b) == sorted(sp2):
            return correct_answer
    return answer

@bot.message_handler(commands=['admin'])
def admin_comand(message):
    admin.admin_command(message)

if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout = 5)