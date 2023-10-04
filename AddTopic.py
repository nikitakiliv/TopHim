import config

import sqlite3
import admin
import os

bot = config.bot


def topic_add(message):
    msg = bot.send_message(message.chat.id, "Введите имя новой темы(или введите 'Нет' для возращения к выбору темы)")
    bot.register_next_step_handler(msg, add_topic)


def add_topic(message):
    # Создаем новую тему с заданным именем
    new_topic = message.text
    if new_topic.lower() == "нет":
        admin.admin_command(message)
    else:
        conn = sqlite3.connect(config.database)
        cursor = conn.cursor()
        # Сохраняем новую тему в базу данных
        cursor.execute("INSERT INTO topics (topic) VALUES (?)", (new_topic,))

        # Получаем id сохраненной темы
        cursor.execute("SELECT last_insert_rowid()")
        new_topic_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        # Запрашиваем у администратора количество вопросов
        bot.send_message(message.chat.id, "Введите количество вопросов:")
        bot.register_next_step_handler(message, lambda m: process_num_questions(m, new_topic_id))


def process_num_questions(message, new_topic):
    num_questions = int(message.text)
    if num_questions <= 0:
        bot.send_message(message.chat.id, "Количество вопросов должно быть положительным числом! Попробуйте еще раз.")
        return
    else:
        add_question(message, new_topic, num_questions, 1)


def add_question(message, new_topic, total_questions, current_question):
    if current_question > total_questions:
        bot.send_message(message.chat.id, "Добавление успешно завершено!")
        return
    # Добавляем новый вопрос
    bot.send_message(message.chat.id, f"Введите текст {current_question}-го вопроса:")
    bot.register_next_step_handler(message, lambda m: add_picture(m, new_topic, total_questions, current_question, m.text))


def add_picture(message, new_topic, total_questions, current_question, question_text):
    bot.send_message(message.chat.id, "Нужно ли добавлять картинку к вопросу? Введите Да/Нет")
    bot.register_next_step_handler(message, lambda m: process_picture_answer(m, new_topic, total_questions, current_question, question_text))


def process_picture_answer(message, new_topic, total_questions, current_question, question_text):
    answer = message.text.lower()
    if answer == "да":
        bot.send_message(message.chat.id, f"Пожалуйста, отправьте изображение {current_question}-го вопроса.")
        bot.register_next_step_handler(message, lambda m: save_picture(m, new_topic, total_questions, current_question, question_text))
    elif answer == "нет":
        picture = None
        add_answer(message, new_topic, total_questions, current_question, question_text, picture)
    else:
        bot.send_message(message.chat.id, "Некорректный ответ. Попробуйте еще раз.")
        add_picture(message, new_topic, total_questions, current_question, question_text)


def save_picture(message, new_topic, total_questions, current_question, question_text):
    if message.photo:
        photo = message.photo[-1].file_id
        file_info = bot.get_file(photo)
        file_extension = file_info.file_path.split(".")[-1]  # Получить расширение файла
        topic_id = new_topic  # Замените на реальное значение ID темы
        question_number = current_question  # Замените на реальное значение номера вопроса
        file_name = f"q_{topic_id}_{question_number}.{file_extension}"
        download_path = f'{config.FilePath}{file_name}'  # Полный путь к файлу
        downloaded_file = bot.download_file(file_info.file_path)
        with open(download_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            bot.send_message(message.chat.id, f"Изображение {file_name} загружено")
        # передаем название файла дальше в функцию сохранения ответа
        bot.send_message(message.chat.id, f"Введите текст ответа на {current_question}-й вопрос:")
        bot.register_next_step_handler(message, lambda m: AskSecondAnswer(m, new_topic, total_questions, current_question, question_text, file_name, m.text))
    else:
        bot.send_message(message.chat.id, "Файл не найден. Попробуйте еще раз.")
        add_picture(message, new_topic, total_questions, current_question, question_text)


def add_answer(message, new_topic, total_questions, current_question, question_text, picture, ):
    bot.send_message(message.chat.id, f"Введите текст ответа на {current_question}-й вопрос:")
    bot.register_next_step_handler(message, lambda m: AskSecondAnswer(m, new_topic, total_questions, current_question, question_text, picture, m.text))


def AskSecondAnswer(message, new_topic, total_questions, current_question, question_text, picture, answer):
    bot.send_message(message.chat.id, f"Нужно ли добавлять второй ответ на {current_question}-й вопрос?\nЕсли да, то введите второй ответ, иначе напишите 'Нет'")
    bot.register_next_step_handler(message, lambda m: AddSecondAnswer(m, new_topic, total_questions, current_question, question_text, picture, answer, m.text))


def AddSecondAnswer(message, new_topic, total_questions, current_question, question_text, picture, answer, second_answer):
    if second_answer.lower() == 'нет':
        second_answer = None
        add_reaction(message, new_topic, total_questions, current_question, question_text, picture, answer, second_answer)
    else:
        add_reaction(message, new_topic, total_questions, current_question, question_text, picture, answer, second_answer)


def add_reaction(message, new_topic, total_questions, current_question, question_text, picture, answer, second_answer):
    bot.send_message(message.chat.id, "Введите 'Да' или 'Нет', является ли ответ реакцией:")
    bot.register_next_step_handler(message, lambda m: save_question_data(m, new_topic, total_questions, current_question, question_text, picture, answer, second_answer, m.text))


def save_question_data(message, new_topic, total_questions, current_question, question_text, picture, answer, second_answer, reaction):
    # Подготавливаем SQL-запрос для вставки данных в таблицу questions
    if reaction.lower() == 'да':
        reaction = 1
    else:
        reaction = 0
    if answer == "-":
        weight = 1
    else:
        weight = 999
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    insert_query = "INSERT INTO questions (topic_id, question, picture, answer, question_number, reaction, secondAnswer, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    values = (new_topic, question_text, picture, answer, current_question, reaction, second_answer, weight)
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()

    # Переходим к добавлению следующего вопроса
    add_question(message, new_topic, total_questions, current_question+1)