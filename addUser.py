import config
import sqlite3
import admin
import telebot.types as types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

bot = config.bot

def choose(message):
    btn_add_user = KeyboardButton("Добавление пользователя")
    btn_delete_user = KeyboardButton("Удаление пользователя")
    markup_add_user = ReplyKeyboardMarkup().add(btn_add_user).add(btn_delete_user)
    msg = bot.send_message(message.chat.id, "Выберите, вы хотите добавить пользователя или удалить?", reply_markup=markup_add_user)
    bot.register_next_step_handler(msg, lambda message: choose_continue(message))


def choose_continue(message):
    if message.text == "Добавление пользователя":
        add_user(message)
    elif message.text == "Удаление пользователя":
        delete_user(message)
    else:
        bot.send_message(message.chat.id, "Введённая вами команда не расспознана, возвращаюсь к главной панели администрирования")
        admin.admin_command(message)


def add_user(message):
    chat_id = message.chat.id
    if message.from_user.id not in config.admin_ids:
        bot.send_message(message.chat.id, "Вы не являетесь администратором!")
        return
    msg = bot.send_message(chat_id, "Введите username пользователя, которого хотите добавить")
    bot.register_next_step_handler(msg, lambda message: add_user_con(message))
    
def add_user_con(message):
    chat_id = message.chat.id
    user_to_add = message.text  # Имя пользователя для добавления
    if not user_to_add:
        bot.send_message(chat_id, "Введите имя пользователя для добавления.")
        return
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь уже в базе данных
    cursor.execute('SELECT username FROM users WHERE username = ?', (user_to_add,))
    existing_user = cursor.fetchone()
    if existing_user:
        bot.send_message(chat_id, f"Пользователь {user_to_add} уже существует.")
        cursor.close()
        conn.close()
        return
    # Добавляем нового пользователя в базу данных
    cursor.execute('INSERT INTO users (username) VALUES (?)', (user_to_add,))
    conn.commit()
    bot.send_message(chat_id, f"Пользователь {user_to_add} успешно добавлен.")
    cursor.close()
    conn.close()
    admin.admin_command(message)  # Возвращаем на главную страницу администрирования


def delete_user(message):
    chat_id = message.chat.id
    if message.from_user.id not in config.admin_ids:
        bot.send_message(message.chat.id, "Вы не являетесь администратором!")
        return
    msg = bot.send_message(chat_id, "Введите username пользователя, которого хотите удалить")
    bot.register_next_step_handler(msg, lambda message: delete_user_con(message))
    
def delete_user_con(message):
    chat_id = message.chat.id
    user_to_delete = message.text  # Имя пользователя для удаления
    if not user_to_delete:
        bot.send_message(chat_id, "Введите имя пользователя для удаления.")
        return
    conn = sqlite3.connect(config.database)
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь в базе данных
    cursor.execute('SELECT username FROM users WHERE username = ?', (user_to_delete,))
    existing_user = cursor.fetchone()
    if not existing_user:
        bot.send_message(chat_id, f"Пользователь {user_to_delete} не найден.")
        cursor.close()
        conn.close()
        return
    # Удаляем пользователя из базы данных
    cursor.execute('DELETE FROM users WHERE username = ?', (user_to_delete,))
    conn.commit()
    bot.send_message(chat_id, f"Пользователь {user_to_delete} успешно удален.")
    cursor.close()
    conn.close()
    admin.admin_command(message)  # Возвращаем на главную страницу администрирования
