import config

import sqlite3
import AddTopic
import telebot.types as types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

bot = config.bot
conn = sqlite3.connect(config.database)
cursor = conn.cursor()


def add(message):
    bot.send_message(message.chat.id, "Выберите тему, в которой хотите добавить вопросы: ", reply_markup=create_inline_buttons_from_db_add())


def create_inline_buttons_from_db_add():
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
            button = InlineKeyboardButton(text=topic, callback_data=f"{id}_add")
            keyboard.append([button])
            button_dict[id] = topic
    reply_markup = InlineKeyboardMarkup(keyboard, row_width=2)
    cursor.close()
    conn.close()

    return reply_markup


def choose_question(chat_id, topic_id):
    msg = bot.send_message(chat_id, "Введите количество вопросов, которые хотите добавить")
    bot.register_next_step_handler(msg, lambda message: process_num_questions(message, topic_id))

def process_num_questions(message, topic_id):
    num_questions = int(message.text)
    if num_questions <= 0:
        bot.send_message(message.chat.id, "Количество вопросов должно быть положительным числом! Попробуйте еще раз.")
        return
    else:
        conn = sqlite3.connect(config.database)
        cursor = conn.cursor()
        cursor.execute('SELECT topic_id, MAX(question_number) AS max_question_number FROM questions WHERE topic_id=?', (topic_id,))
        max_question_number = cursor.fetchall()
        max_question_number = max_question_number[0][1]
        num_questions += int(max_question_number)
        cursor.close()
        conn.close()
        AddTopic.add_question(message, topic_id, num_questions, max_question_number + 1)
