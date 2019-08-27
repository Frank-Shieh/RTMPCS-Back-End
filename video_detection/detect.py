"""Yolo v3 detection script.

Saves the detections in the `detection` folder.

Usage:
    python detect.py <images/video> <iou threshold> <confidence threshold> <filenames>

Example:
    python detect.py images 0.5 0.5 data/images/dog.jpg data/images/office.jpg
    python detect.py video 0.5 0.5 data/video/shinjuku.mp4

Note that only one video can be processed at one run.
"""

import tensorflow as tf
import cv2,os

from .yolo_v3 import Yolo_v3
from .utils import load_class_names, draw_frame

_MODEL_SIZE = (416, 416)
_CLASS_NAMES_FILE = './video_detection/coco.names'
_MAX_OUTPUT_SIZE = 20


def yolo_detection(iou_threshold, confidence_threshold, input_names, outputDirPath):
    class_names = load_class_names(_CLASS_NAMES_FILE)
    n_classes = len(class_names)

    model = Yolo_v3(n_classes=n_classes, model_size=_MODEL_SIZE,
                    max_output_size=_MAX_OUTPUT_SIZE,
                    iou_threshold=iou_threshold,
                    confidence_threshold=confidence_threshold)

    inputs = tf.placeholder(tf.float32, [1, *_MODEL_SIZE, 3])
    detections = model(inputs, training=False)
    saver = tf.train.Saver(tf.global_variables(scope='yolo_v3_model'))
    people_number = 0

    with tf.Session() as sess:
        saver.restore(sess, './video_detection/weights/model.ckpt')

        win_name = 'Video detection'
        cv2.namedWindow(win_name)
        cap = cv2.VideoCapture(input_names)
        frame_size = (cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                      cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        fps = cap.get(cv2.CAP_PROP_FPS)
        outputPath = os.path.join(outputDirPath, os.path.basename(input_names))
        outputPath = str(outputPath.replace("\\", "/"))
        out = cv2.VideoWriter(outputPath, fourcc, fps,
                              (int(frame_size[0]), int(frame_size[1])))

        try:
            totalFrames = 0.
            while True:
                ret, frame = cap.read()
                if totalFrames % 2 == 0:
                    if not ret:
                        break
                    resized_frame = cv2.resize(frame, dsize=_MODEL_SIZE[::-1],
                                               interpolation=cv2.INTER_NEAREST)
                    detection_result = sess.run(detections,
                                                feed_dict={inputs: [resized_frame]})

                    # print("detection_result", detection_result)
                    people_number = draw_frame(frame, frame_size, detection_result,
                               class_names, _MODEL_SIZE, people_number)

                    cv2.imshow(win_name, frame)

                    key = cv2.waitKey(1) & 0xFF

                    if key == ord('q'):
                        break

                    out.write(frame)
                totalFrames = totalFrames + 1
        finally:
            cv2.destroyAllWindows()
            cap.release()
            print('Detections have been saved successfully.')
    return outputPath, people_number
