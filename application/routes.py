from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from flask import render_template, flash, redirect, url_for, request, send_from_directory, send_file
from flask_login import current_user, login_user, logout_user, login_required
from .forms import ResetPasswordRequestForm
from .email import send_password_reset_email
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from . import app, db
from .models import User, Video, History, Message
from .forms import LoginForm, RegistrationForm, ResetPasswordForm
from .utils import run_detection
import json
import os
import requests

executor = ThreadPoolExecutor(2)

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template("index.html", title='Home Page', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.username.data, email=form.email.data, status=1, role_id=1)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['inputFile']
    basePath = os.path.join('/data', current_user.__getattr__('name'), 'source')
    if not os.path.exists(basePath):
        os.makedirs(basePath)
        os.chmod(basePath, mode=0o777)
    # 文件名尚未更改，多文件上传尚未实现
    uploadPath = os.path.join(basePath, secure_filename(os.path.splitext(file.filename)[0]+'-'+str(datetime.now().strftime("%Y/%m/%d-%H:%M:%S"))+os.path.splitext(file.filename)[1]))
    if uploadPath.endswith(('.mp4', '.mkv', '.avi', '.wmv', '.iso')):
        file.save(uploadPath)
        uploadPath = str(uploadPath.replace("\\", "/"))
        username = current_user.__getattr__('name')
        # 异步处理
        executor.submit(run_detection, 0.5, 0.5, uploadPath, file.filename, username)
        upload_status = 'saved'
        return render_template('index.html', upload_status = upload_status)
    else:
        upload_status = 'Error Format'
        return render_template('index.html', upload_status=upload_status)


@app.route('/retrieve_history', methods=['GET', 'POST'])
def retrieve_history():
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    histories = db.session.query(History, Video).filter(History.video_id == Video.id).filter_by(user_id=user.id, status=1).all()
    # histories = History.query.filter_by(user_id=user.id, status = 1).all()
    return render_template('history.html', histories=histories)


@app.route('/downloadVideo/<path:id>', methods=['GET', 'POST'])
def downloadVideo(id):
    videoLocation = db.session.query(Video.location).filter_by(id=id).first()
    r = requests.get(videoLocation[0])
    videoIO = BytesIO(r.content)
    return send_file(videoIO, as_attachment=True, attachment_filename='result.mp4', mimetype='video/mp4')


@app.route('/deleteVideo/<path:id>', methods=['GET', 'POST'])
def deleteVideo(id):
    history = History.query.filter_by(id=id).first()
    history.status = 0
    db.session.flush()
    db.session.commit()
    return redirect(url_for('retrieve_history'))



@app.route('/retrieve_notification', methods=['GET', 'POST'])
def retrieve_notification():
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    print(user.last_message_read_time)
    if user.last_message_read_time is None:
        notifications = Message.query.filter_by(user_id=user.id, ).all()
    else:
        notifications = Message.query.filter_by(user_id=user.id, )\
            .filter(Message.time_stamp > user.last_message_read_time).all()
    user.last_message_read_time = datetime.now()
    db.session.flush()
    db.session.commit()
    messages = {}
    counter = 0
    for msg in notifications:
        messages[counter] = msg.to_json()
        counter = counter + 1
    return json.dumps(messages)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)