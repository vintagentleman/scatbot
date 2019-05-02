import logging
from logging import config
from pathlib import Path

from yaml import load, Loader


def config_logger(name):
    conf_path = Path.joinpath(Path(__file__).resolve().parents[1], 'conf', 'logging.yaml')

    with conf_path.open() as conf_file:
        config.dictConfig(load(conf_file, Loader=Loader))

    return logging.getLogger(name)


logger = config_logger('scatbot')
