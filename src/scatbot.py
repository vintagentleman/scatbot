import os
import sys

import psycopg2
import yaml
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from utils import logger, get_db_url


class Bot:

    def _start_callback(self, update, context):
        logger.info('User {} started bot'.format(update.effective_user['id']))
        context.bot.send_message(chat_id=update.message.chat_id, text=self._answers['start'])

    def _echo_callback(self, update, context):
        logger.info('User {} echoed {}'.format(update.effective_user['id'], update.message.text))
        context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

    def __init__(self):
        self._token = os.getenv('TOKEN')
        self._db_conn = psycopg2.connect(os.environ['DATABASE_URL'] if MODE == 'prod' else get_db_url('scatbot'))
        self._updater = Updater(self._token, use_context=True, request_kwargs={'proxy_url': os.getenv('PROXY')})

        self._updater.dispatcher.add_handler(CommandHandler('start', self._start_callback))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self._echo_callback))

        with open('answers.yaml', encoding='utf-8') as answers_conf:
            self._answers = yaml.load(answers_conf, Loader=yaml.Loader)

    def run(self):
        logger.info('Starting bot')

        if MODE == 'dev':
            self._updater.start_polling()
        else:
            port = int(os.environ.get('PORT', '8443'))
            heroku_app_name = os.environ.get('HEROKU_APP_NAME', 'scatbot')
            self._updater.start_webhook(listen='0.0.0.0', port=port, url_path=self._token)
            self._updater.bot.set_webhook('https://{}.herokuapp.com/{}'.format(heroku_app_name, self._token))

        self._updater.idle()


if __name__ == '__main__':
    MODE = os.getenv('MODE')

    if MODE not in ('dev', 'prod'):
        logger.error('Invalid MODE value. Aborting')
        sys.exit(1)

    Bot().run()
