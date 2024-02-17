import logging
import requests

from telebot import types, TeleBot

from my_token import my_token, api_key

# Setup logging to file
logging.basicConfig(filename='log.txt', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = TeleBot(my_token)

# Instead of calling API here, we will call it inside functions to ensure fresh rates.
url = "https://api.currencyfreaks.com/v2.0/rates/latest?apikey={}"


# bot configuration and start/help commands
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Я бот для конвертации валют.')


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, '/start - запустить бота\n/help - помощь\n/convert - конвертировать валюты')


@bot.message_handler(commands=['convert'])
def convert_command(message):
    bot.send_message(message.chat.id, 'Введите сумму:')
    bot.register_next_step_handler(message, handle_amount_input)


def handle_amount_input(message):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError("Число должно быть больше 0.")

        # Storing the amount in the user's dictionary (assuming chat.id is your definition for a user)
        user_data[message.chat.id] = {'amount': amount}

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('USD/EUR', callback_data='USD/EUR')
        btn2 = types.InlineKeyboardButton('EUR/USD', callback_data='EUR/USD')
        btn3 = types.InlineKeyboardButton('RUB/EUR', callback_data='RUB/EUR')
        btn4 = types.InlineKeyboardButton('RUB/USD', callback_data='RUB/USD')
        btn5 = types.InlineKeyboardButton('Другие валюты', callback_data='else')
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id, 'Выберите пару валют', reply_markup=markup)
    except ValueError as e:
        logger.warning(f"User entered a bad amount: {message.text} - Error: {e}")
        bot.send_message(message.chat.id, 'Неверный формат или число <= 0.')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'else':  # If user wants to input custom currencies
        bot.send_message(call.message.chat.id, 'Введите пару валют через слэш (например, USD/EUR)')
        bot.register_next_step_handler(call.message, handle_custom_conversion)
    else:  # User tapped a button with predefined currency pair
        handle_conversion(call)


def handle_conversion(call):
    user_id = call.message.chat.id
    # Ensure that you've properly defined user_data somewhere globally
    amount = user_data.get(user_id, {}).get('amount')

    if not amount:
        logger.error(f"No amount saved for user {user_id}")
        bot.send_message(call.message.chat.id, "Произошла ошибка, попробуйте еще раз.")
        return

    # Extract currencies from callback data
    from_currency, to_currency = call.data.split('/')

    # Call the API within this function to get fresh rates
    response = requests.get(url.format(api_key) + f"&symbols={from_currency},{to_currency}")
    data = response.json()

    if response.status_code == 200:
        rates = data['rates']
        result = amount / float(rates[from_currency]) * float(rates[to_currency])
        bot.send_message(call.message.chat.id, f"{amount} {from_currency} = {result:.2f} {to_currency}")
    else:
        logger.error(f"Failed to retrieve exchange rates: {response.status_code}")
        bot.send_message(call.message.chat.id, "Ошибка при получении данных о курсах валют.")


def handle_custom_conversion(message):
    try:
        from_currency, to_currency = message.text.strip().upper().split('/')
        user_id = message.chat.id

        # Ensure that you've properly defined user_data somewhere globally
        amount = user_data.get(user_id, {}).get('amount')

        if not amount:
            logger.error(f"No amount saved for user {user_id}")
            bot.send_message(message.chat.id, "Произошла ошибка, попробуйте еще раз.")
            return

        # Call the API within this function to get fresh rates
        response = requests.get(url.format(api_key) + f"&symbols={from_currency},{to_currency}")
        data = response.json()

        if response.status_code == 200:
            rates = data['rates']
            result = amount / float(rates[from_currency]) * float(rates[to_currency])
            bot.send_message(message.chat.id, f"{amount} {from_currency} = {result:.2f} {to_currency}")
        else:
            logger.error(f"Failed to retrieve exchange rates: {response.status_code}")
            bot.send_message(message.chat.id, "Ошибка при получении данных о курсах валют.")
    except Exception as e:
        logger.error(f"Error in custom currency handling: {e}")
        bot.send_message(message.chat.id, 'Неверный формат. Введите пару валют через слэш (например, USD/EUR)')


# Initialize user_data storage
user_data = {}


@bot.message_handler(func=lambda message: True)
def greeting_goodbye_message(message):
    text = message.text.lower()
    if 'прив'.lower() in text:
        bot.send_message(message.chat.id, 'Привет! Чем могу помочь сегодня?')
    elif 'до свид'.lower() in text or 'пока' in text:
        bot.send_message(message.chat.id, 'До свидания! Буду рад видеть тебя снова!')


bot.polling(none_stop=False, interval=0)
