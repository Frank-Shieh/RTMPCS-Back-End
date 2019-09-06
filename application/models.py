from . import db
from time import time
import jwt
from . import app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import login
from datetime import datetime


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return '<Roles {}>'.format(self.name)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.Integer, unique=True, nullable=False)
    messages_received = db.relationship('Message', foreign_keys='Message.user_id', backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return '<Name {}>'.format(self.name)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.time_stamp > last_read_time).count()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def to_json(self):
        json_data = {
            'id': self.id,
            'name': self.name,
            'password': self.password,
            'email' : self.email,
            'status': self.status,
            'role_id': self.role_id,
            'messages_received': self.messages_received,
            'last_message_read_time': self.last_message_read_time
        }
        return json_data

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Video(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key= True)
    location = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200), nullable=True)

    def to_json(self):
        json_data = {
            'id': self.id,
            'location': self.location,
            'name': self.name
        }
        return json_data


class History(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    video_id = db.Column(db.Integer, nullable=False)
    submit_time = db.Column(db.DATETIME, nullable=True)
    status = db.Column(db.Integer, nullable=False)

    def to_json(self):
        json_data = {
            'id': self.id,
            'user_id': self.user_id,
            'count': self.count,
            'video_id': self.video_id,
            'submit_time': self.submit_time.strftime("%Y/%m/%d, %H:%M"),
            'status': self.status
        }
        return json_data


class Message(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    time_stamp = db.Column(db.DATETIME, nullable=True)

    def __repr__(self):
        return '<Message {}>'.format(self.content)

    def to_json(self):
        json_data = {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'time_stamp': self.time_stamp.strftime("%Y/%m/%d, %H:%M")
        }
        return json_data


@login.user_loader
def load_user(id):
    return User.query.get(int(id))