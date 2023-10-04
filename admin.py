import config

import AddTopic
import sqlite3
import ReworkTopic
import AddQuestionsToTopic
import addUser
import checkStats
import telebot.types as types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = config.bot
# устанавливаем соединение с базой данных
conn = sqlite3.connect(config.database)
cursor = conn.cursor()

def admin_command(message):
    first_name = message.chat.first_name
    if message.from_user.id not in config.admin_ids:
        bot.send_message(message.chat.id, "Вы не являетесь администратором!")
        return
    btn_1_admin = KeyboardButton("Добавление новой темы")
    btn_2_admin = KeyboardButton("Редактирование темы")
    btn_3_admin = KeyboardButton("Добавление вопросов в сущестующие темы")
    btn_4_admin = KeyboardButton("Добавление/удаление пользователя")
    btn_5_admin = KeyboardButton("Просмотр статистики учеников")
    murkup_admin = ReplyKeyboardMarkup().add(btn_1_admin).add(btn_2_admin).add(btn_3_admin).add(btn_4_admin).add(btn_5_admin)
    msg = bot.send_message(message.chat.id, f"Приветствую {first_name}. Выберите действие, которое хотите сделать.", reply_markup=murkup_admin)
    bot.register_next_step_handler(msg, lambda message: inline_callback_handler(message))

def inline_callback_handler(message):
    if message.text == 'Добавление новой темы':
        AddTopic.topic_add(message)
    elif message.text == 'Редактирование темы':
        ReworkTopic.rework(message)
    elif message.text == 'Добавление вопросов в сущестующие темы':
        AddQuestionsToTopic.add(message)
    elif message.text == 'Добавление/удаление пользователя':
        addUser.choose(message)
    elif message.text == 'Просмотр статистики учеников':
        checkStats.view_user_statistics(message)
    else:
        bot.send_message(message.from_user.id, 'К сожалению, я не могу обработать ваш запрос.')