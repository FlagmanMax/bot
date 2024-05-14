import logging
import sqlite3
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from datetime import datetime
import calendar
import telebot
from telebot import types
from config import token

PAGE_TIMEOUT = 10

# Инициализация бота
bot = telebot.TeleBot(token)

# Инициализация логгера
logging.basicConfig(level=logging.INFO,
                    encoding='UTF - 8',
                    filename='bot.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Produce correct ending for noun of the second declension
def ending(value):
    end = 'ов'
    if (value or (value % 100)) in (11, 12, 13, 14):
        end = 'ов'
    else:
        if value % 10 in (2, 3, 4):
            end = 'а'
        elif value % 10 == 1:
            end = ''
    return end


def wait_for_element(driver, path):
    try:
        element_present = EC.presence_of_element_located((By.XPATH, path))
        element = WebDriverWait(driver, PAGE_TIMEOUT).until(element_present)
    except TimeoutException:
        print("Page download error")
        element = None
    return element

# # Инициализация базы данных
# conn = sqlite3.connect('telegram_bot_data.db')
# cursor = conn.cursor()
#
# # Создание таблицы для хранения информации о пользователях
# cursor.execute('''CREATE TABLE IF NOT EXISTS users (
#                   id INTEGER PRIMARY KEY,
#                   username TEXT,
#                   first_name TEXT,
#                   last_name TEXT
#                   )''')
#
# # Создание таблицы для хранения данных об активности пользователей
# cursor.execute('''CREATE TABLE IF NOT EXISTS user_activity (
#                   user_id INTEGER,
#                   activity_date TEXT,
#                   activity_count INTEGER
#                   )''')
# conn.commit()

device_types = [
    ('корректор', 'ЭК270'),
    ('корректор', 'ТК220'),
    ('комплекс', 'СГ-ТКР'),
    ('комплекс', 'СГ-ЭКР'),
]
call_period = {
    "currentMonth": " текущий месяц ",
    "lastMonth": " прошлый месяц ",
    "currentYear": " текущий год ",
    "lastYear": " прошлый год ",
}
commands = {  # command description used in the "help" command
    '/start':    'Сообщение приветствия',
    '/help':     'Список команд',
    'ЭК270':    'Получить число поверенных корректоров ЭК270',
    'ТК220':    'Получить число поверенных корректоров ТК220',
    'СГ-ЭКР':   'Получить число поверенных комплексов СГ-ЭКР',
    'СГ-ТКР':   'Получить число поверенных комплексов СГ-ТКР',
}
url = f'https://fgis.gost.ru/fundmetrology/cm/results?filter_mi_mitype={device_types[0][1]}'
selected_option = list(call_period)[2]

logging.warning('New start!')

# create webdriver object
# options = webdriver.ChromeOptions()
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# download strategy: none
options.page_load_strategy = 'none'

# get web driver
driver = webdriver.Chrome(options=options)

# set timeout for page opening
driver.set_page_load_timeout(PAGE_TIMEOUT)
try:
    driver.get(url)
except TimeoutException as e:
    logging.exception("Bot started: page not found - exception")
logging.info('Bot started: page opened')

# wait for element to download
element = wait_for_element(driver, "//button[@class='btn btn-primary']")
if element:
    element.click()
    logging.info('Pop-up window closed')
else:
    print('No pop-up window')
    logging.info('No pop-up window')

def get_data(device_type, period):
    # make URL for each device type and time period
    date_now = datetime.now().date()
    current_year = date_now.year
    current_month = date_now.month
    match period:
        case "currentMonth":
            (_, days_per_month) = calendar.monthrange(current_year, current_month)
            start = f'{current_year}-{current_month}-01'
            stop = f'{current_year}-{current_month}-{days_per_month}'
        case "lastMonth":
            if current_month == 1:
                last_month = 12
                current_year = current_year - 1
            else:
                last_month = current_month - 1
            (_, days_per_month) = calendar.monthrange(current_year, last_month)
            start = f'{current_year}-{last_month}-01'
            stop = f'{current_year}-{last_month}-{days_per_month}'
        case "currentYear":
            start = f'{current_year}-01-01'
            stop = f'{current_year}-12-31'
        case "lastYear":
            current_year = date_now.year - 1
            start = f'{current_year}-01-01'
            stop = f'{current_year}-12-31'
            pass
        case _:
            start = f'{current_year}-01-01'
            stop = f'{current_year}-12-31'

    url = f'https://fgis.gost.ru/fundmetrology/cm/results?\
filter_mi_mitype={device_type[1]}\
&filter_verification_date_start={start}\
&filter_verification_date_end={stop}\
&activeYear={current_year}'

    print(url)

    try:
        driver.get(url)
    except TimeoutException:
        None

    # wait for element to download
    element = wait_for_element(driver, "//div[@class='col-md-18 col-36 block_pagination_stat']")
    if element is None:
        print('Page download error')
        result = "Нет данных"
        return result

    answer = []
    answer = element.text.split()

    result = f'{datetime.now().time().strftime("%H:%M:%S")}: Поверено {answer[4]} {device_type[0]}{ending(int(answer[4]))} {device_type[1]} '

    print(result)

    return result


def DB(message):
    user_info = message.from_user
    user_id = user_info.id
    username = user_info.username
    first_name = user_info.first_name
    last_name = user_info.last_name

    # # Анонимизация данных пользователя (для примера - просто удаляем фамилию)
    # last_name = None
    global cursor
    # Сохранение информации о пользователе в базу данных
    cursor.execute("INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                   (user_id, username, first_name, last_name))
    conn.commit()

# Функция для записи активности пользователя
def log_user_activity(user_id, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global cursor
    cursor.execute("INSERT INTO user_activity (user_id, timestamp, message) VALUES (?, ?, ?)", (user_id, timestamp, message))
    conn.commit()

@bot.message_handler(commands=['start'])
# handle the "/start" command
def handle_start(message):
    # DB(message)

    # Приветствие
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     f'Привет {message.from_user.first_name}! \r\n\
Это чат-бот для выгрузки количества поверок СИ из ФГИС "Аршин".')

    # Создание фильтра
    show_filter(message, False)
    logging.info(f'Start command; user = {message.from_user.first_name}')


@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    help_text = "Доступны следующие команды: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += key + ":\t "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    device_type = ('прибор', message.text)
    logging.info(f'user = {message.from_user.first_name};'
                 f' source = keyboard;'
                 f' text = {message.text};'
                 f' interval = {selected_option}')

    res_0 = get_data(device_type, selected_option)
    res_1 = call_period[selected_option]

    bot.send_message(message.chat.id, text=res_0 + res_1)
    logging.info(f'result = {res_0} за {res_1}')

    show_filter(message, False)



# Обработка выбора периода
@bot.callback_query_handler(func=lambda call: call.data in call_period.keys())
def filter_callback(call):
    global selected_option
    selected_option = call.data
    bot.answer_callback_query(call.id, text="Выбрано: " + call.data)
    show_filter(call.message, True)
    print(selected_option)


# Обработка выбора типа СИ
@bot.callback_query_handler(func=lambda call: True)
def device_type_inline(call):
    global selected_option
    print(call.data)
    for device_type in device_types:
        if device_type[1] == call.data:

            logging.info(f'user = {call.message.from_user.first_name};'
                         f' source = button;'
                         f' device = {call.data};'
                         f' interval = {selected_option}')

            res_0 = get_data(device_type, selected_option)
            res_1 = call_period[selected_option]

            bot.send_message(call.message.chat.id, text=res_0 + ' за ' + res_1)
            logging.info(f'result = {res_0} за {res_1}')

            break
    else:
        # Действия при получении другого сообщения
        bot.send_message(call.message.chat.id, text='Укажите другой тип СИ')

    # Создание фильтра
    show_filter(call.message, False)

def show_filter(message, update_indicator):

    global selected_option

    # Выбор интервала поиска
    global call_period

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    #
    # currentMonth = telebot.types.InlineKeyboardButton(
    #     "" + (" ✅ " if selected_option == "currentMonth" else "") + "Текущий месяц",
    #     callback_data="currentMonth")
    # lastMonth = telebot.types.InlineKeyboardButton(
    #     "" + (" ✅" if selected_option == "lastMonth" else "") + "Прошлый месяц",
    #     callback_data="lastMonth")
    # currentYear = telebot.types.InlineKeyboardButton(
    #     "" + (" ✅" if selected_option == "currentYear" else "") + "Этот год",
    #     callback_data="currentYear")
    # lastYear = telebot.types.InlineKeyboardButton(
    #     "" + (" ✅" if selected_option == "lastYear" else "") + "Прошлый год",
    #     callback_data="lastYear")
    # keyboard.add(currentMonth, lastMonth, currentYear, lastYear)

    radio_buttons = []
    for k, v in call_period.items():
        radio_buttons.append(
            telebot.types.InlineKeyboardButton(
                f'{" ✅ " if selected_option == k else ""} {v}',
                callback_data=k
                )
            )
    keyboard.add(radio_buttons[0], radio_buttons[1], radio_buttons[2], radio_buttons[3])

    # Выбор типа устройства
    for device_type in device_types:
        button = types.InlineKeyboardButton(device_type[1], callback_data=device_type[1])
        keyboard.add(button)

    # Отправка сообщения или обновление фильтра
    if update_indicator:
        bot.edit_message_reply_markup(message.chat.id,
                                      message.message_id,
                                      reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Введите интервал времени поиска и тип устройства (кнопкой или с клавиатуры):", reply_markup=keyboard)

    return keyboard


bot.polling()