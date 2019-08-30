from video_detection.detect import yolo_detection
import os
from .models import Video, User, History, Message
from . import app, db
from .email import send_notification_email
from datetime import datetime


def run_detection(iou_threshold, confidence_threshold, source_address, username):
    basePath = os.path.split(os.path.dirname(source_address))[0]
    outputDirPath = os.path.join(basePath, 'output')
    if not os.path.exists(outputDirPath):
        os.makedirs(outputDirPath)
    # run yolo3 detection
    outputFilePath, people_number = yolo_detection(iou_threshold, confidence_threshold, source_address, outputDirPath)

    newVideo = Video(location=outputFilePath, name=os.path.basename(outputFilePath))
    db.session.add(newVideo)
    db.session.flush()
    # get video id
    video_id = newVideo.id
    # get current user id
    user = User.query.filter_by(name=username).first()
    send_notification_email(user)
    # add history
    newHistory = History(user_id=user.id, count=people_number,
                         video_id=video_id, submit_time=datetime.now(), status= 1)
    db.session.add(newHistory)

    # send notification to user
    msg_content = os.path.basename(outputFilePath)+" completed."
    msg = Message(recipient=user, content=msg_content)
    db.session.add(msg)
    db.session.commit()


