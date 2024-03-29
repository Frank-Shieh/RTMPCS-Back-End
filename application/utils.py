import threading
import jpush
from video_detection.detect import yolo_detection
import os, sys
from .models import Video, User, History, Message
from . import app, db, _jpush
from .email import send_notification_email
from datetime import datetime


def run_detection(iou_threshold, confidence_threshold, source_address, source_file_name, username, app_request):
    basePath = os.path.split(os.path.dirname(source_address))[0]

    outputDirPath = os.path.join(basePath, 'output')
    if not os.path.exists(outputDirPath):
        os.makedirs(outputDirPath)
        os.chmod(outputDirPath, mode=0o777)
    # run yolo3 detection
    outputFilePath, people_number = yolo_detection(iou_threshold, confidence_threshold, source_address, outputDirPath)
    # add IP server location
    outputFilePath = 'http://45.113.234.163:8009'+outputFilePath[5:]
    newVideo = Video(location=outputFilePath, name=source_file_name)
    db.session.add(newVideo)
    db.session.flush()
    # get video id
    video_id = newVideo.id
    # get current user id
    user = User.query.filter_by(name=username).first()
    # add history
    newHistory = History(user_id=user.id, count=people_number,
                         video_id=video_id, submit_time=datetime.now(), status=1)
    db.session.add(newHistory)
    # send notification to user
    msg_content = os.path.basename(outputFilePath)+" completed."
    msg = Message(recipient=user, content=msg_content, time_stamp=datetime.now())
    db.session.add(msg)
    db.session.commit()
    if app_request == 'true':
        # send notification to APP
        push = _jpush.create_push()
        push.audience = jpush.audience(jpush.alias(username))
        push.notification = jpush.notification(alert="Video Completed!")
        push.platform = jpush.all_
        push.send()
    else:
        # send email to user
        send_notification_email(user)
    sys.exit()


