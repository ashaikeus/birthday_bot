import telebot
import sqlite3
from random import randint
from string import ascii_uppercase
from datetime import datetime
from time import sleep
from threading import Thread
from secrets import TOKEN  # Secrets is a file filled with, well, secrets:
                           # tokens, potentially unsafe info and such!

# Creating a connection to the bot
bot = telebot.TeleBot(TOKEN)

group = None
user_id = None

lang_ru = False  # Default bot language is English
# Some two-language text constants to use later...
data_change_success_message = [("An error occured. Try again?", "Произошла ошибка. Попробуйте ещё раз."),
                               ("Changes saved successfully.", "Изменения успешно сохранены.")]
EMOJIS = ('🥳', '🎂', '🎉', '🎁', '🎈')


# Functions that do not respond to commands and messages sent by the user
def start(message):
    start_message = ["Welcome to @kylebrea's birthday bot!\
                    \n\nThis bot aims to help you remember the birthdays of your colleagues and subordinates.\
                    \nPress /help to get the list of commands.",
                     "Добро пожаловать в бот для поздравлений с днями рождения от @kylebrea!\
                    \n\nЭтот бот предназначен для информирования и уведомления о днях рождениях коллег.\
                    \nДля вывода списка команд нажмите на /help."
                     ]
    bot.send_message(message.chat.id, start_message[lang_ru])


def join_or_create(message):
    joc_message = ["Do you want to join a group or create one?",
                   "Вы хотите присоединиться к существующей группе или создать свою?"]
    markup_text = [("Join a group", "Присоединиться к группе"),
                   ("Create a group", "Создать группу")]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton(markup_text[0][lang_ru], callback_data='join_group'),
               telebot.types.InlineKeyboardButton(markup_text[1][lang_ru], callback_data='create_group'))
    bot.send_message(message.chat.id, joc_message[lang_ru], reply_markup=markup)


def verify_group(message):
    global group
    msg = ('Invalid code', 'Неправильный код')
    group_code = message.text.strip().upper()
    conn = sqlite3.connect('birthdays.sql')
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{group_code}'")
    table_exists = cur.fetchone()
    cur.close()
    conn.close()
    try:
        if table_exists:
            group = group_code
        else:
            raise Exception
    except Exception:
        bot.send_message(message.chat.id, msg[lang_ru])
        bot.register_next_step_handler(message, verify_group)
    finally:
        print('verify_group done')


def verify_name_birthday(message):
    msg = data_change_success_message[0]
    try:
        name, surname, bday = message.text.split()
        day, month, year = bday.split('.')
        if len(message.text.split()) != 3 or len(bday.split('.')) != 3:
            raise Exception
        if len(day) != 2 or len(month) != 2 or len(year) != 4:
            print('bad length')
            raise Exception
        elif int(day) > 31 or int(month) > 12 or int(year) > 2024:
            print('out of limits date')
            raise Exception
        conn = sqlite3.connect('birthdays.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE {group} SET name='{name}', surname='{surname}', day='{day}',\
        month='{month}', year='{year}' WHERE id='{message.from_user.id}'")
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        bot.send_message(message.chat.id, msg[lang_ru])
        bot.register_next_step_handler(message, verify_name_birthday)
    finally:
        print('verify_name_birthday done')


def look_for_birthdays():
    while True:
        if group:
            today, tomonth, toyear = datetime.now().day, datetime.now().month, datetime.now().year
            print(today, tomonth, toyear)
            conn = sqlite3.connect('birthdays.sql')
            cur = conn.cursor()
            cur.execute(f"SELECT name, surname, year FROM {group} WHERE day='{today}' AND month='{tomonth}'")
            birthdays = cur.fetchall()
            for bday in birthdays:
                msg = (f"Today is {bday[0]} {bday[1]}'s {toyear - bday[-1]}th birthday!",
                       f"Сегодня {bday[0]} {bday[1]} отмечает {toyear - bday[-1]}летие!")
                bot.send_message(user_id, msg[lang_ru])
        sleep(30)  # should be updated every hour, I left this value 30 seconds for practice


# Functions with message handlers that respond to user's commands
@bot.message_handler(commands=['start'])
def init(message):
    global lang_ru, user_id
    lang_ru = message.from_user.language_code == 'ru'
    user_id = message.from_user.id
    start(message)
    join_or_create(message)


@bot.message_handler(commands=['set_name_birthday'])
def set_name_birthday(message):
    msg = ["Enter your full name separated by spaces and date of birth strictly in DD.MM.YYYY format\
(like this: Aleksandra Semenenia 21.03.2004):",
           "Введите своё полное имя, разделённое запятыми, и день рождения в формате ДД.ММ.ГГГГ\
(пример: Александра Семененя 21.03.2004):"]
    bot.send_message(message.chat.id, msg[lang_ru])
    bot.register_next_step_handler(message, verify_name_birthday)


@bot.message_handler(commands=['change_language'])
def change_language(message):
    global lang_ru
    lang_ru = not lang_ru
    start(message)


@bot.message_handler(commands=['all_birthdays'])
def all_birthdays(message):
    if not group:
        bot.send_message(message.chat.id, data_change_success_message[0][lang_ru])
        return
    msg = ('No birthdays found', 'Не найдено дней рождения')
    conn = sqlite3.connect('birthdays.sql')
    cur = conn.cursor()
    cur.execute(f"SELECT name, surname, day, month, year FROM {group} ORDER BY month, day, year")
    birthdays = cur.fetchall()
    result = '' if len(birthdays) > 0 else msg[lang_ru]
    for i in range(len(birthdays)):
        result += f"{i + 1}. {birthdays[i][0]} {birthdays[i][1]} - {birthdays[i][2]}.{birthdays[i][3]}.{birthdays[i][4]}\n"
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['join_group'])
def join_group(message):
    msg = ("Enter the 6-letter group code your group admin sent you:",
           'Введите шестибуквенный код, который вам отправил администратор группы:')
    bot.reply_to(message, msg[lang_ru])
    bot.register_next_step_handler(message, verify_group)


@bot.message_handler(commands=['create_group'])
def create_group(message):
    global group
    conn = sqlite3.connect('birthdays.sql')
    cur = conn.cursor()
    group_code = ''.join([ascii_uppercase[randint(0, 25)] for i in range(6)])
    cur.execute(f'CREATE TABLE IF NOT EXISTS {group_code} (id int primary_key unique, name varchar(50), surname varchar(50), day int, month int, year int)')
    conn.commit()
    cur.close()
    conn.close()
    group = group_code
    msg = (f"You have successfully created a group.\
            \nYour group's code is **{group_code}**, send it to people who want to join it!",
           f'Вы успешно создали группу, теперь другие пользователи могут к ней подключиться.\
           \nКод вашей группы: **{group_code}**, перешлите его пользователям, которых хотите включить в группу!')
    bot.send_message(message.chat.id, msg[lang_ru], parse_mode='markdown')


@bot.message_handler(commands=['register'])
def register(message):
    if not group:
        print('no group')
        bot.send_message(message.chat.id, data_change_success_message[0][lang_ru])
        return
    conn = sqlite3.connect('birthdays.sql')
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {group} WHERE id='{message.from_user.id}'")
    user_exists = cur.fetchone()
    if not user_exists:
        cur.execute(f"INSERT INTO {group} (id, name, surname, day, month, year)\
                VALUES ('{message.from_user.id}', '{message.from_user.first_name}', '{message.from_user.last_name}',\
                '00', '00', '0000')")
    conn.commit()
    cur.close()
    conn.close()
    register_message = ["This bot needs an account to work properly, please create one:",
                        "Чтобы пользоваться ботом, пройдите короткую регистрацию."]
    bot.send_message(message.chat.id, register_message[lang_ru])
    set_name_birthday(message)


@bot.message_handler(commands=['help'])
def help(message):
    msg = ("1. Join a group (/join_group) or create one (/create_group);\
    \n2. Register using /register;\
    \n3. Now you are automatically subscribed to all your group's members' birthdays.\
    \nYou'll receive notifications for their birthday, and you can view a list using /all_birthdays.",
           "1. Присоединитесь к группе (/join_group) либо создайте свою (/create_group);\
    \n2. Введите личные данные через /register;\
    \n3. Теперь вы подписаны на дни рождения всех членов группы.\
    \nВы будете получать уведомления об их днях рождения. Посмотреть весь список: /all_birthdays.",)
    bot.send_message(message.chat.id, msg[lang_ru])


# Default message handler, should be placed last
@bot.message_handler()
def invalid_command(message):
    invalid_message = ["Invalid message! Try /help for available commands",
                       "В сообщении нет команды! /help содержит все ключевые слова, на которые отвечает бот"]
    bot.send_message(message.chat.id, invalid_message[lang_ru])


# Callback manager
@bot.callback_query_handler(func=lambda callback: True)
def callback_manager(callback):
    if callback.data == 'join_group':
        join_group(callback.message)
    elif callback.data == 'create_group':
        create_group(callback.message)


# Making the bot run for ever and ever
if __name__ == '__main__':
    t = Thread(target=look_for_birthdays)
    t.start()
    bot.polling(none_stop=True)
