import os
import sys
from collections import Counter, namedtuple

import psycopg2
import yaml
from psycopg2.extras import Json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from utils import logger, get_db_url


Task = namedtuple('Task', ['stem_id', 'word'])


class Bot:

    def _send_task(self, update, context):
        with self._db_conn, self._db_conn.cursor() as curs:
            curs.execute('SELECT id FROM stems WHERE completed = FALSE ORDER BY random() LIMIT 1;')
            stem_id = curs.fetchone()[0]
            curs.execute('SELECT word FROM words WHERE stem_id = %s;', (stem_id,))
            self._current_task = Task(stem_id, curs.fetchone()[0])

        context.bot.send_message(chat_id=update.message.chat_id, text=self._current_task.word)
        logger.info('User {} received task {}'.format(update.message.chat_id, self._current_task.word))

    def _save_answer(self, answer):
        with self._db_conn, self._db_conn.cursor() as curs:
            curs.execute('SELECT answers FROM stems WHERE id = %s;', (self._current_task.stem_id,))
            data = curs.fetchone()[0]

            answers = Counter(data) if data is not None else Counter()
            answers[answer] += 1

            curs.execute(
                'UPDATE stems SET answers = %s, completed = %s WHERE id = %s;',
                (Json(answers), sum(answers.values()) > 5, self._current_task.stem_id)
            )

    def _start_callback(self, update, context):
        logger.info('User {} started bot'.format(update.effective_user['id']))
        context.bot.send_message(chat_id=update.message.chat_id, text=self._answers['start'])
        self._send_task(update, context)

    def _answer_callback(self, update, context):
        logger.info('User {} answered {}'.format(update.effective_user['id'], update.message.text))
        self._save_answer(update.message.text.upper())
        self._send_task(update, context)

    def __init__(self):
        self._token = os.getenv('TOKEN')
        self._db_conn = psycopg2.connect(os.environ['DATABASE_URL'] if MODE == 'prod' else get_db_url('scatbot'))
        self._updater = Updater(self._token, use_context=True, request_kwargs={'proxy_url': os.getenv('PROXY')})

        self._updater.dispatcher.add_handler(CommandHandler('start', self._start_callback))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self._answer_callback))

        with open('answers.yaml', encoding='utf-8') as answers_conf:
            self._answers = yaml.load(answers_conf, Loader=yaml.Loader)
        self._current_task = None

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
