from flask_mail import Message
from flask import render_template
from application import mail
from . import app
from threading import Thread
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.header import Header


#using flask_mail Module
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body, sync=False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[People-Counter] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


#using smtp Module
def send_notification_email(user):
    mail_host = 'smtp.qq.com'
    mail_user = '382095390'
    mail_pass = 'utaqwjnajauwbjai'
    sender = '382095390@qq.com'
    recipients = [user.email]
    content ='Dear '+ user.name+', \n\nYour video detection is completed.' \
             'Now you can check it in history. \n\nSincerely,\n\nThe People-Counter Team'
    message = MIMEText(content, 'plain', 'utf-8')
    message['Subject'] = '[People-Counter] Notification'
    message['From'] = sender
    message['To'] = recipients[0]
    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(
            sender, recipients, message.as_string())
        smtpObj.quit()
    except smtplib.SMTPException as e:
        print('error', e)
