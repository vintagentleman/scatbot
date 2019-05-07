import os
import sys
import random
import subprocess
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yaml

from orm import User, Task, Word, Answer
from utils import LOGGER, session_scope


class Bot:

    @property
    def _db_url(self):
        if MODE == 'prod':
            return os.environ['DATABASE_URL']

        proc = subprocess.run(
            'heroku config:get DATABASE_URL -a scatbot', capture_output=True, shell=True, text=True
        )

        if proc.returncode != 0 or proc.stdout is None:
            LOGGER.error('Failed to retrieve Heroku database URL. Aborting')
            sys.exit(1)
        else:
            LOGGER.info('Successfully retrieved Heroku database URL')
            return proc.stdout.strip()

    @staticmethod
    def _send_message(update, context, text, buttons=[]):
        if isinstance(text, list):
            text = random.choice(text)
        reply_markup = None if not buttons else ReplyKeyboardMarkup(
            [[KeyboardButton(button)] for button in buttons], resize_keyboard=True, one_time_keyboard=True
        )
        context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_markup)

    def _send_task(self, update, context):
        """
        Get a random unfinished task and assign it to the current user.
        """
        with session_scope(self._session) as session:
            task = session.query(Task).filter_by(completed=False).order_by(func.random()).first()

            if task is None:
                self._send_message(update, context, self._answers['all_tasks_complete'])
                return

            word = session.query(Word).filter_by(task_id=task.id).order_by(func.random()).first()
            session.query(User).filter_by(id=update.effective_user.id).one().current_task = task.id
            self._send_message(update, context, word.string, word.options)
            LOGGER.info('User {} received task {}'.format(update.effective_user.username, word.string))

    def _save_answer(self, update):
        """
        Get the current task and associate it with the answer provided.
        If the latter does not exist, add it, otherwise increase its total.
        Mark the task as completed if the total of the answers given exceeds 5.
        """
        with session_scope(self._session) as session:
            task_id = session.query(User).filter_by(id=update.effective_user.id).one().current_task
            answer = session.query(Answer).filter_by(task_id=task_id).one_or_none()

            if answer is None:
                session.add(Answer(task_id=task_id, string=update.message.text.upper()))
            else:
                answer.total += 1

            total = session.query(func.sum(Answer.total)).filter_by(task_id=task_id).scalar()
            session.query(Task).filter_by(id=task_id).one().completed = total > 5
            session.query(User).filter_by(id=update.effective_user.id).one().tasks_done += 1

    def _start_callback(self, update, context):
        LOGGER.info('User {} started bot'.format(update.effective_user.username))
        self._send_message(update, context, self._answers['start'])

        with session_scope(self._session) as session:
            if not session.query(User).filter_by(id=update.effective_user.id).count():
                session.add(User(id=update.effective_user.id, name=update.effective_user.username))

        self._send_task(update, context)

    def _answer_callback(self, update, context):
        LOGGER.info('User {} answered {}'.format(update.effective_user.username, update.message.text))
        self._save_answer(update)
        self._send_task(update, context)

    def _skip_callback(self, update, context):
        self._send_task(update, context)

    def _help_callback(self, update, context):
        self._send_message(update, context, self._answers['help'])

    def _catchall_callback(self, update, context):
        self._send_message(update, context, self._answers['catchall'])

    def __init__(self):
        self._token = os.getenv('TOKEN')
        self._engine = sa.create_engine(self._db_url)
        self._session = sessionmaker(self._engine)

        self._updater = Updater(self._token, use_context=True, request_kwargs={
            'proxy_url': os.getenv('PROXY')
        })
        self._updater.dispatcher.add_handler(CommandHandler('start', self._start_callback))
        self._updater.dispatcher.add_handler(CommandHandler('help', self._help_callback))
        self._updater.dispatcher.add_handler(CommandHandler('skip', self._skip_callback))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'[А-я+]'), self._answer_callback))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self._catchall_callback))

        with Path.joinpath(Path(__file__).parent, 'answers.yaml').open(encoding='utf-8') as answers_conf:
            self._answers = yaml.load(answers_conf, Loader=yaml.Loader)

    def run(self):
        LOGGER.info('Starting bot')

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
        LOGGER.error('Invalid MODE value. Aborting')
        sys.exit(1)

    Bot().run()
