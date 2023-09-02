import traceback

from telebot import TeleBot

from settings import settings

bot = TeleBot(token=settings.telegram_token.get_secret_value())


def safe_send(message):
    try:
        bot.send_message(settings.chat_id, message)
    except Exception as e:
        traceback.print_exc()
