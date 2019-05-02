import sys
import logging
import subprocess
from logging import config
from pathlib import Path

from yaml import load, Loader


def get_db_url(name):
    proc = subprocess.run(f'heroku config:get DATABASE_URL -a {name}', capture_output=True, shell=True, text=True)

    if proc.returncode != 0 or proc.stdout is None:
        logger.error('Failed to retrieve Heroku database URL. Aborting')
        sys.exit(1)
    else:
        logger.info('Successfully retrieved Heroku database URL')
        return proc.stdout.strip()


def config_logger(name):
    with Path.joinpath(Path(__file__).resolve().parents[1], 'conf', 'logging.yaml').open() as logging_conf:
        config.dictConfig(load(logging_conf, Loader=Loader))
    return logging.getLogger(name)


logger = config_logger('scatbot')
