import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:0769@localhost/people_counter'
    SQLALCHEMY_TRACK_MODIFICATIONS = False