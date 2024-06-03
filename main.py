import telebot
from secrets import TOKEN  # Secrets is a file filled with, well, secrets:
                           # tokens, potentially unsafe info and such!

# Creating a connection to the bot
bot = telebot.TeleBot(TOKEN)

# Some two-language text constants to use later...
data_change_success_message = [("An error occured. Try again?", "Произошла ошибка. Попробуйте ещё раз."),
                               ("Changes saved successfully.", "Изменения успешно сохранены.")]


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


def register(message):
    register_message = ["This bot needs an account to work properly, please create one:",
                        "Чтобы пользоваться ботом, пройдите короткую регистрацию."]
    bot.send_message(message.chat.id, register_message[lang_ru])
    set_name(message)
    set_birthday(message)


def join_or_create(message):
    joc_message = ["Do you want to join a group or create one?",
                   "Вы хотите присоединиться к существующей группе или создать свою?"]
    markup_text = [("Join a group", "Присоединиться к группе"),
                   ("Create a group", "Создать группу")]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton(markup_text[0][lang_ru], callback_data='join_group'),
               telebot.types.InlineKeyboardButton(markup_text[1][lang_ru], callback_data='create_group'))
    bot.send_message(message.chat.id, joc_message[lang_ru], reply_markup=markup)


# Functions with message handlers that respond to user's commands
@bot.message_handler(commands=['start'])
def init(message):
    global lang_ru
    lang_ru = message.from_user.language_code == 'ru'
    start(message)
    register(message)
    join_or_create(message)


@bot.message_handler(commands=['set_name'])
def set_name(message):
    msg = ["Enter your full name and surname:", "Введите своё полное имя и фамилию:"]
    bot.send_message(message.chat.id, msg[lang_ru])


@bot.message_handler(commands=['set_birthday'])
def set_birthday(message):
    msg = ["Enter your date of birth strictyly in DD.MM.YYYY format (like this: 21.03.2004):",
           "Введите свой день рождения в формате ДД.ММ.ГГГГ (пример: 21.03.2004):"]
    bot.send_message(message.chat.id, msg[lang_ru])


@bot.message_handler(commands=['change_language'])
def change_language(message):
    global lang_ru
    lang_ru = not lang_ru
    start(message)


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
    bot.polling(none_stop=True)
