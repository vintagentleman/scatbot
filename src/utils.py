from contextlib import contextmanager
import logging
from logging import config
from pathlib import Path

from yaml import load, Loader


def config_logger(name):
    with Path.joinpath(Path(__file__).resolve().parents[1], 'conf', 'logging.yaml').open() as logging_conf:
        config.dictConfig(load(logging_conf, Loader=Loader))
    return logging.getLogger(name)


@contextmanager
def session_scope(factory):
    session = factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


LOGGER = config_logger('scatbot')
