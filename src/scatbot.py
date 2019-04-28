import os
import sys

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from handlers import *
from utils import logger

TOKEN = os.getenv('TOKEN')
mode = os.getenv('MODE')

if mode == 'dev':
    def run(app):
        app.start_polling()
elif mode == 'prod':
    def run(app):
        PORT = int(os.environ.get('PORT', '8443'))
        HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME')
        app.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
        app.bot.set_webhook('https://{}.herokuapp.com/{}'.format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error('Invalid MODE value')
    sys.exit(1)


if __name__ == '__main__':
    logger.info('Starting bot')
    updater = Updater(TOKEN, use_context=True, request_kwargs={
        'proxy_url': os.getenv('PROXY')
    })

    updater.dispatcher.add_handler(CommandHandler('start', start_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo_handler))

    run(updater)
