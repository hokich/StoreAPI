import telebot
from django.conf import settings


def send_message_from_telegram_bot(chat_id: str, text_msg: str) -> None:
    """Sends a message to a specified Telegram chat using the bot token."""
    bot = telebot.TeleBot(token=settings.TG_BOT_TOKEN)
    bot.send_message(chat_id, text_msg, parse_mode="HTML")
    return None
