import logging
from os import path
from logging import config

from yaml import load, Loader


def config_logger(name):
    conf_path = path.join(
        path.dirname(path.realpath(__file__)), '..', 'conf', 'logging.yaml'
    )

    with open(conf_path) as conf_file:
        config.dictConfig(load(conf_file, Loader=Loader))

    return logging.getLogger(name)


logger = config_logger('scatbot')
