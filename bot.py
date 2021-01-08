import logging
import os
import sys
import json

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram

InlineKeyboardButton = telegram.InlineKeyboardButton

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
        logger.info("Up and ready to go on heroku!")
else:
    logger.error("No MODE specified!")
    sys.exit(1)


# open JSON file containing bot commands
with open('commands.json') as f:
  data = json.load(f)


def start_handler(update, context):
    # Creating a handler-function for /start command
    chat_id = update.message.chat_id
    logger.info("User {} started bot".format(chat_id))
    # Options to interact with sticker packs that user created through Stitch
    keyboard = [InlineKeyboardButton(text='New sticker pack', callback_data='new'),
                InlineKeyboardButton(text='Show sticker packs', callback_data='show'),
                InlineKeyboardButton(text='Edit sticker pack', callback_data='edit'),
                InlineKeyboardButton(text='Delete Sticker pack', callback_data='delete')]
    # Format inline keyboard options into a column
    reply_markup = telegram.InlineKeyboardMarkup.from_column(keyboard)
    update.message.reply_text("hello world \nClick /help for a list of commands", reply_markup=reply_markup)

def help_handler(update, context):
    # Create a handler-function /help command
    commands = data['Commands'].keys()
    text = ""
    for i in commands:
        # Uncapitalise JSON keys to be outputted
        text += "/{}\n".format(i.lower())
    update.message.reply_text("These are the commands supported by the bot\n{}".format(text))

def button(update, context):
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    query.answer()

    if query.data == 'new':
        query.message.reply_text('New sticker pack')
    elif query.data == 'show':
        query.message.reply_text('Show sticker packs')
    elif query.data == 'edit':
        query.message.reply_text('Edit sticker pack')
    elif query.data == 'delete':
        query.message.reply_text('Delete Sticker pack')


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("help", help_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    run(updater)