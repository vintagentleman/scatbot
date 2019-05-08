from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    tasks_done = sa.Column(sa.SmallInteger, default=0)
    created_at = sa.Column(sa.DateTime, default=datetime.now())
    current_task = sa.Column(sa.Integer, sa.ForeignKey('tasks.id'))


class Task(Base):
    __tablename__ = 'tasks'

    id = sa.Column(sa.Integer, primary_key=True)
    stem = sa.Column(sa.String, unique=True, nullable=False)
    lemma = sa.Column(sa.String)


class Word(Base):
    __tablename__ = 'words'

    id = sa.Column(sa.Integer, primary_key=True)
    task_id = sa.Column(sa.Integer, sa.ForeignKey('tasks.id'))
    string = sa.Column(sa.String, unique=True, nullable=False)
    morph = sa.Column(sa.ARRAY(sa.String), nullable=False)
    options = sa.Column(sa.ARRAY(sa.String))


class Answer(Base):
    __tablename__ = 'answers'

    id = sa.Column(sa.Integer, primary_key=True)
    task_id = sa.Column(sa.Integer, sa.ForeignKey('tasks.id'))
    string = sa.Column(sa.String, unique=True, nullable=False)
    total = sa.Column(sa.SmallInteger, default=0)
