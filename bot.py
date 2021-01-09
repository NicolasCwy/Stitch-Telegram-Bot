import logging
import os
import sys
import json
import re
import hashlib

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, Handler
import telegram
from telegram import ReplyKeyboardMarkup

from processImg import processImg

InlineKeyboardButton = telegram.InlineKeyboardButton
ENTRY, ENTER_NAME, AWAIT_IMAGE = range(3)

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
with open('commands.json') as f:
    data = json.load(f)

def start_handler(update, context):
    reply_keyboard = [['Create'],['Cancel']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    logger.info("Started")

    chat_id = update.message.chat_id
    logger.info("User {} started bot".format(chat_id))

    update.message.reply_text(data['Commands']['Start']['Text'], reply_markup=markup)
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
    file = update.message.photo[-1].get_file()
    file.download('img/{}.jpg'.format(file.file_unique_id))
    try:
        processImg('img/{}.jpg'.format(file.file_unique_id))
    except Exception:
        update.message.reply_text(data['Commands']['photoError']['Text'])
        return ENTRY

    stickerImg = open("img/r_{}.png".format(file.file_unique_id), 'rb')
    # show the user the cropped image
    # update.message.reply_photo(stickerImg)

    # create/add to sticker pack and return sticker
    username = update.message.from_user['username']
    hash = hashlib.sha1(bytearray(update.effective_user.id)).hexdigest()
    sticker_set_name = 'Stitched_%s_by_stichers_bot' % hash[:10]

    #TODO get emoji from user

    context.user_data['sticker-set-name'] = sticker_set_name
    logging.info("creating sticker for: userid: {}, stickersetname: {}".format(update.message.from_user.id, sticker_set_name))
    try:
        context.bot.addStickerToSet(user_id=update.message.from_user.id, name=sticker_set_name, emojis='😄',
                                    png_sticker=open("img/r_{}.png".format(file.file_unique_id), 'rb'))
    except Exception:
        context.bot.createNewStickerSet(user_id=update.message.from_user.id, name=sticker_set_name,
            title=context.user_data['name'], emojis='😄', png_sticker=open("img/r_{}.png".format(file.file_unique_id), 'rb'))
    finally:
        update.message.reply_text(data['Commands']['nextSticker']['Text'])
        return AWAIT_IMAGE


def validate_pack_name(name):
    return 1 < len(name) < 64

def name_handler(update, context):
    pack_name = update.message.text
    logger.info("I'm at ENTER_NAME")
    update.message.reply_text(data['Commands']['nameConfirmation']['Text'] + "{}".format(pack_name))
    context.user_data['name'] = pack_name
    if validate_pack_name(pack_name):
        update.message.reply_text("Name is valid! " + data['Commands']['newPackAddSticker']['Text'])
        return AWAIT_IMAGE
    else:
        update.message.reply_text(data['Commands']['nameError']['Text'])
        return ENTER_NAME

def publish_handler(update, context):
    update.message.reply_text(data['Commands']['finalizePack']['Text'])
    update.message.reply_text(data['Commands']['createPack']['Text'] + "\n https://t.me/addstickers/{}".format(context.user_data['sticker-set-name']))

def cancel(update, context):
    update.message.reply_text(data['Commands']['cancel']['Text'])
    return ENTRY

def check_user_input(update, context):
    user_input = update.message.text
    logger.info("User input was {}".format(user_input))
    if "Create" in user_input:
        update.message.reply_text(data['Commands']['namePack']['Text'])
        return ENTER_NAME
    elif "Cancel" in user_input:
        update.message.reply_text(data['Commands']['exit']['Text'])
    else:
        # ask again
        reply_keyboard = [['Create'],['Cancel']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(
            ("{}?! ".format(user_input) + data['Commands']['askAgain']['Text']),
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
                            name_handler, pass_user_data=True)],
            AWAIT_IMAGE: [MessageHandler(Filters.photo, image_handler, pass_user_data=True), CommandHandler("publish", publish_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_handler))

    run(updater)