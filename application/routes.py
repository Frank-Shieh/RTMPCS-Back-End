from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, FIRST_COMPLETED
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
import threading


executor = ThreadPoolExecutor(1)
@app.route('/app/hello', methods=['GET', 'POST'])
def app_hello():
    if current_user.is_authenticated:
        return "Hello!!"
    else:
        return "No hello!"


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # user is already login
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    # user login and verify user information
    if request.method == "POST":
        user_info = request.form.to_dict()
        user = User.query.filter_by(name=user_info.get("username")).first()
        if user is None or not user.check_password(user_info.get("password")):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_pate = url_for('home')
        return redirect(url_for('home'))
    return render_template('signin.html', title='Sign In')

@login_required
@app.route('/index', methods=['GET', 'POST'])
def home():
    return render_template('home.html', title='home')


@app.route('/account', methods=['GET', 'POST'])
def account():
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    return render_template('account.html', user=user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        # verify request form data
        user_info = request.form.to_dict()
        check_user = User.query.filter_by(name=user_info.get("username")).first()
        email = User.query.filter_by(email = user_info.get("email")).first()
        if check_user is not None:
            flash("Username has existed")
            return redirect(url_for("register"))
        if user_info.get("password") != user_info.get("rpassword"):
            flash("Passwords are different")
            return redirect(url_for("register"))
        if email is not None:
            flash("Email has registered")
            return redirect(url_for("register"))
        user = User(name=user_info.get("username"), email=user_info.get("email"), status=1, role_id=1)
        # update user password
        user.set_password(user_info.get("password"))
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title='signup')


@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == "GET":
        return render_template('upload.html', title='Upload File')
    else:
        file = request.files['file']
        #basePath = os.path.join('/data', current_user.__getattr__('name'), 'source')
        basePath = os.path.join(os.getcwd(), current_user.__getattr__('name'), 'source')
        if not os.path.exists(basePath):
            os.makedirs(basePath)
            os.chmod(basePath, mode=0o777)
        uploadPath = os.path.join(basePath, secure_filename(os.path.splitext(file.filename)[0]+'-'+str(datetime.now().strftime("%Y/%m/%d-%H:%M:%S"))+os.path.splitext(file.filename)[1]))
        # check file type
        if uploadPath.endswith(('.mp4', '.mkv', '.avi', '.wmv', '.iso')):
            file.save(uploadPath)
            uploadPath = str(uploadPath.replace("\\", "/"))
            username = current_user.__getattr__('name')
            # asynchronous process
            threading.Thread(target=run_detection, args=(0.5, 0.5, uploadPath, file.filename, username, ), daemon=True).start()
            flash('File upload successfully')
        else:
            flash('Error file format')
        return redirect(url_for('upload'))

@app.route('/history',methods=['GET', 'POST'])
def history():
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    histories = db.session.query(History, Video).filter(History.video_id == Video.id).filter_by(user_id=user.id, status=1).all()
    return render_template('history.html',histories=histories)


@app.route('/downloadVideo/<path:id>', methods=['GET', 'POST'])
def downloadVideo(id):
    # get the location of video and download
    videoLocation = db.session.query(Video.location).filter_by(id=id).first()
    r = requests.get(videoLocation[0])
    videoIO = BytesIO(r.content)
    return send_file(videoIO, as_attachment=True, attachment_filename='result.mp4', mimetype='video/mp4')


@app.route('/deleteVideo/<path:id>', methods=['GET', 'POST'])
def deleteVideo(id):
    # delete corresponding history of video
    history = History.query.filter_by(id=id).first()
    history.status = 0
    db.session.flush()
    db.session.commit()
    return redirect(url_for('history'))


@app.route('/retrieve_notification', methods=['GET', 'POST'])
def retrieve_notification():
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    # judge the time of last reading of user
    if user.last_message_read_time is None:
        notifications = Message.query.filter_by(user_id=user.id, ).all()
    else:
        notifications = Message.query.filter_by(user_id=user.id, )\
            .filter(Message.time_stamp > user.last_message_read_time).all()
    # update last reading time
    user.last_message_read_time = datetime.now()
    db.session.flush()
    db.session.commit()
    messages = {}
    counter = 0
    # packing the information into json format
    for msg in notifications:
        messages[counter] = msg.to_json()
        counter = counter + 1
    return json.dumps(messages)


@app.route('/refresh_notification', methods=['GET', 'POST'])
def refresh_notification():
    # count the unread message number
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    messages = {}
    counter = user.new_messages()
    messages[0] = counter
    return json.dumps(messages)


@app.route('/forget', methods=['GET', 'POST'])
def forget():
    # forget password page operation
    if request.method == "POST":
        email_info = request.form.to_dict()
        user = User.query.filter_by(email=email_info.get("email")).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for the instructions to reset your password')
            return render_template('signin.html', title='Sign In')
        else:
            flash('Please input a valid Email')
            return render_template('forget.html', title='Forget Password')
    else:
        return render_template('forget.html', title='Forget Password')


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # send an email to user and provide a link to reset password
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # reset password before the user login
    # verify the token
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Error URL')
        return redirect(url_for('login'))
    if request.method == "POST":
        user_info = request.form.to_dict()
        if user_info.get("password") == user_info.get("rpassword"):
            user.set_password(user_info.get("password"))
            db.session.commit()
            flash('Your password has been reset.')
            return redirect(url_for('login'))
        else:
            flash('Passwords are different')
    return render_template('resetpassword.html', title="Reset Password")


@app.route('/reset',methods=['GET','POST'])
def reset():
    # reset password after the user login
    user = User.query.filter_by(name=current_user.__getattr__('name')).first()
    if request.method == "POST":
        user_info = request.form.to_dict()
        if user_info.get("password") == user_info.get("rpassword"):
            user.set_password(user_info.get("password"))
            db.session.commit()
            return render_template('account.html', user=user)
        else:
            flash('Passwords are different')
    return render_template('reset.html', user=user)
