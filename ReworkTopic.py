import config

import os
import sqlite3
import admin
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

bot = config.bot
conn = sqlite3.connect(config.database)
cursor = conn.cursor()


def rework(message):
    bot.send_message(message.chat.id, "Выберите тему, в которой хотите изменить вопрос/ответ: ", reply_markup = create_inline_buttons_from_db_rework())


def create_inline_buttons_from_db_rework():
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
            button = InlineKeyboardButton(text=topic, callback_data=f"{id}_rework")
            keyboard.append([button])
            button_dict[id] = topic
    reply_markup = InlineKeyboardMarkup(keyboard, row_width=2)
    cursor.close()
    conn.close()

    return reply_markup


def choose_question(chat_id, topic_id):
    msg = bot.send_message(chat_id, "Введите номер вопроса, который хотите изменить")
    bot.register_next_step_handler(msg, lambda message: question(message, topic_id, message.text))


def question(message, topic_id, question_number):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    cursor.execute('SELECT topic_id, MAX(question_number) AS max_question_number FROM questions WHERE topic_id=?', (topic_id,))
    max_question_number = cursor.fetchall()
    max_question_number = max_question_number[0][1]
    if int(question_number) <= max_question_number:
        cursor.execute('SELECT question, picture, answer FROM questions WHERE topic_id = ? AND question_number = ?', (topic_id, question_number))
        row = cursor.fetchone()
        if not row:
            return
        question, picture, answer = row
        ask_rework_question(message, topic_id, question_number, answer, picture, question)
    else:
        bot.send_message(message, "Такого вопроса нет в данной теме")
        choose_question(message, topic_id)
    cursor.close()
    conn.close()

def ask_rework_question(message, topic_id, question_number, answer, picture, question):
    msg = bot.send_message(message.chat.id, f"Данный вопрос сейчас выглядит вот так:\n{question}\nЕсли вы хотите его поменять, введите новый текст вопроса, иначе введите 'Нет' для продолжения исправления")
    bot.register_next_step_handler(msg, lambda message: rework_question(message, topic_id, question_number, answer, picture, question, message.text))


def rework_question(message, topic_id, question_number, answer, picture, old_question, new_question):
    if new_question.lower() == 'нет':
        ask_rework_picture(message, topic_id, question_number, answer, old_question,  picture)
    else:
        ask_rework_picture(message, topic_id, question_number, answer, new_question, picture)

def ask_rework_picture(message, topic_id, question_number, answer, question, picture):
    if picture:
        picture_path = f"{config.FilePath}{picture}"
        if os.path.isfile(picture_path):
            with open(picture_path, 'rb') as f:
                bot.send_photo(message.chat.id, f)
        msg = bot.send_message(message.chat.id, "Хотите ли поменять картинку в этом вопросе? Если да, то напишите 'Да', иначе напишите 'Нет'")
        bot.register_next_step_handler(msg, lambda message: rework_picture(message, topic_id, question_number, answer, question, picture))
    else:
        msg = bot.send_message(message.chat.id, "В данном вопросе нет картинки. Хотите ли её добавить?")
        bot.register_next_step_handler(msg, lambda message: rework_picture(message, topic_id, question_number, answer, question, picture))

def rework_picture(message, topic_id, question_number, answer, question, picture):
    answer_picture = message.text.lower()
    if answer_picture == "да":
        bot.send_message(message.chat.id, f"Пожалуйста, отправьте изображение {question_number}-го вопроса.")
        bot.register_next_step_handler(message, lambda m: save_picture(m, topic_id, question_number, answer, question))
    elif answer_picture == "нет":
        if picture:
            picture_path = f"{config.FilePath}{picture}"
            if os.path.isfile(picture_path):
                rework_answer(message, topic_id, question_number, answer, question, picture)
        else:
            picture = None
            rework_answer(message, topic_id, question_number, answer, question, picture)
    else:
        bot.send_message(message.chat.id, "Некорректный ответ. Попробуйте еще раз.")
        bot.register_next_step_handler(message, lambda message: rework_picture(message, topic_id, question_number, answer, question, picture))

def save_picture(message, topic_id, question_number, answer, question):
    if message.photo:
        photo = message.photo[-1].file_id
        file_info = bot.get_file(photo)
        file_extension = file_info.file_path.split(".")[-1]  # Получить расширение файла
        file_name = f"q_{topic_id}_{question_number}.{file_extension}"
        download_path = f'{config.FilePath}{file_name}'  # Полный путь к файлу
        downloaded_file = bot.download_file(file_info.file_path)
        with open(download_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            bot.send_message(message.chat.id, f"Изображение {file_name} загружено")
        bot.send_message(message.chat.id, f"Ответ на данный вопрос:\n{answer}\nХотите ли вы его поменять?:")
        bot.register_next_step_handler(message, lambda m: save_question_data(m, topic_id, question_number, answer, question, file_name, m.text))
    else:
        bot.send_message(message.chat.id, "Файл не найден. Попробуйте еще раз.")
        bot.register_next_step_handler(message, lambda message: rework_picture(message, topic_id, question_number, answer, question))


def rework_answer(message, topic_id, question_number, answer, question, picture):
    bot.send_message(message.chat.id, f"Ответ на данный вопрос:\n{answer}\nХотите ли вы его поменять?")
    bot.register_next_step_handler(message, lambda m: save_question_data(m, topic_id, question_number, answer, question, picture, m.text))


def save_question_data(message, topic_id, question_number, answer, question, picture, new_answer):
    if new_answer.lower() == 'нет':
        conn = sqlite3.connect(config.database)
        cursor = conn.cursor()
        if answer == "-":
            weight = 1
        else:
            weight = 999
        cursor.execute("UPDATE questions SET question = ?, answer = ?, picture = ?, weight = ? WHERE topic_id = ? AND question_number = ?",
               (question, answer, picture, weight, topic_id, question_number))
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_message(message.chat.id, "Данные сохранены")
        admin.admin_command(message)
    elif new_answer.lower() == 'да':
        bot.send_message(message.chat.id, "Введите новый ответ на вопрос")
        bot.register_next_step_handler(message, lambda m: save_all_data(m, topic_id, question_number, question, picture, m.text))
    else: 
        bot.send_message(message.chat.id, "Некорректный ввод. Попробуйте ещё раз")
        bot.register_next_step_handler(message, lambda m: save_question_data(m, topic_id, question_number, answer, question, picture, m.text))



def save_all_data(message, topic_id, question_number, question, picture, answer):
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    if answer == "-":
        weight = 1
    else:
        weight = 999
    cursor.execute("UPDATE questions SET question = ?, answer = ?, picture = ?, weight = ? WHERE topic_id = ? AND question_number = ?",
            (question, answer, picture, weight, topic_id, question_number))
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, "Данные сохранены")
    admin.admin_command(message)