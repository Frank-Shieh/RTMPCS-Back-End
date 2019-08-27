from concurrent.futures import ThreadPoolExecutor

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from . import app, db
from .models import User, Video
from .forms import LoginForm, RegistrationForm
from .utils import run_detection
import os

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
        user = User(name=form.username.data, status=1, role_id= 1)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['inputFile']
    basePath = os.path.join(os.path.dirname(__file__), current_user.__getattr__('name'), 'source')
    if not os.path.exists(basePath):
        os.makedirs(basePath)
    # 文件名尚未更改，多文件上传尚未实现
    uploadPath = os.path.join(basePath, secure_filename(file.filename))
    file.save(uploadPath)
    uploadPath = str(uploadPath.replace("\\", "/"))
    username = current_user.__getattr__('name')
    # 异步处理
    executor.submit(run_detection, 0.5, 0.5, uploadPath, username)

    upload_status = 'saved'

    return render_template('index.html', upload_status = upload_status)

