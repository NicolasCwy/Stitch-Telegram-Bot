import logging
import os
import random
import sys
import json

from telegram.ext import Updater, CommandHandler

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
    update.message.reply_text("hello world \n click /random for a random number")

def random_handler(update, context):
    # Creating a handler-function for /random command
    number = random.randint(0, 10)
    chat_id = update.message.chat_id
    logger.info("User {} number {} ".format(chat_id, number))
    update.message.reply_text("Random number: {}".format(number))

def help_handler(update, context):
    # Create a handler-function /help command
    commands = data['commands'].keys()
    text = ""
    for i in commands:
        text += "/{}\n".format(i)
    update.message.reply_text("These are the commands supported by the bot\n{}".format(text))

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("random", random_handler))
    dispatcher.add_handler(CommandHandler("help", help_handler))

    run(updater)