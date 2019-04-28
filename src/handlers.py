from utils import logger


def start_handler(update, context):
    logger.info('User {} started bot'.format(update.effective_user['id']))
    context.bot.send_message(chat_id=update.message.chat_id, text='Hello world!')


def echo_handler(update, context):
    logger.info('User {} echoed {}'.format(update.effective_user['id'], update.message.text))
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
