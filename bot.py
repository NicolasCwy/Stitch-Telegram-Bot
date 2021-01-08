import logging
import os
import sys
import json

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram
from telegram import ReplyKeyboardMarkup

from processImg import processImg

InlineKeyboardButton = telegram.InlineKeyboardButton
ENTRY, AWAIT_IMAGE, ENTER_NAME = range(3)

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
        updater.idle()
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
with open('commands.json','r') as f:
    data = json.load(f)

def start_handler(update, context):
    reply_keyboard = [['Name'],['Image'],['Cancel']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    logger.info("Started")

    chat_id = update.message.chat_id
    logger.info("User {} started bot".format(chat_id))

    # Options to interact with sticker packs that user created through Stitch
    keyboard = [InlineKeyboardButton(text='New sticker pack', callback_data='new'),
                InlineKeyboardButton(text='Show sticker packs', callback_data='show'),
                InlineKeyboardButton(text='Edit sticker pack', callback_data='edit'),
                InlineKeyboardButton(text='Delete Sticker pack', callback_data='delete')]
    # Format inline keyboard options into a column
    reply_markup = telegram.InlineKeyboardMarkup.from_column(keyboard)
    update.message.reply_text(data['Commands']['Start']['Text'], reply_markup=reply_markup)

    return ENTRY

def help_handler(update, context):
    # Create a handler-function /help command
    commands = data['Commands'].keys()
    text = ""
    for i in commands:
        # Uncapitalise JSON keys to be outputted
        text += "/{}\n".format(i.lower())
    update.message.reply_text(data['Commands']['Help']['Text'] + "{}".format(text))

def image_handler(update, context):
    logger.info("recvd something")
    file = update.message.photo[-1].get_file()
    file.download('img/{}.jpg'.format(file.file_unique_id))
    logger.info('user image {}'.format(file))
    update.message.reply_text(data['Commands']['nextSticker']['Text'])
    #TODO send image to algorithm
    processImg('img/{}.jpg'.format(file.file_unique_id))
    update.message.reply_photo(open("img/r_{}.png".format(file.file_unique_id), 'rb'))

def name_handler(update, context):
    #TODO: verify name and send to API
    logger.info("I'm at ENTER_NAME")
    update.message.reply_text(data['Commands']['nameConfirmation']['Text'] + "{}".format(update.message.text))
    return ENTRY

def skip_photo(update, context):
    update.message.reply_text(data['Commands']['skip']['Text'])
    return ENTRY

def cancel(update, context):
    update.message.reply_text(data['Commands']['cancel']['Text'])

def check_user_input(update, context):
    user_input = update.message.text
    logger.info("User input was {}".format(user_input))
    if "Name" in user_input:
        update.message.reply_text(data['Commands']['namePack']['Text'])
        return ENTER_NAME
    elif "Image" in user_input:
        update.message.reply_text(data['Commands']['newPackAddSticker']['Text'])
        return AWAIT_IMAGE
    else:
        # ask again
        reply_keyboard = [['Name'],['Image'],['Cancel']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(
            ("{}?!" + data['Commands']['askAgain']['Text']".format(
            user_input)),
            reply_markup=markup)
        return ENTRY

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        states={
            ENTRY: [MessageHandler(Filters.text,
                                   check_user_input)],
            ENTER_NAME: [MessageHandler(Filters.text,
                            name_handler)],
            AWAIT_IMAGE: [MessageHandler(Filters.photo, image_handler), CommandHandler('skip', skip_photo)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_handler))

    run(updater)