"""Contains utility functions for Yolo v3 model."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from seaborn import color_palette
import cv2
from .trackingModule.centroidtracker import CentroidTracker
from .trackingModule.trackableobject import TrackableObject
import dlib

# instantiate our centroid tracker, then initialize a list to store
# each of our dlib correlation trackers, followed by a dictionary to
# map each unique object ID to a TrackableObject
ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
trackers = []
trackableObjects = {}


def load_class_names(file_name):
    """Returns a list of class names read from `file_name`."""
    with open(file_name, 'r') as f:
        class_names = f.read().splitlines()
    return class_names


def draw_frame(frame, frame_size, boxes_dicts, class_names, model_size, people_number):
    """Draws detected boxes in a video frame.
    Args:
        frame: A video frame.
        frame_size: A tuple of (frame width, frame height).
        boxes_dicts: A class-to-boxes dictionary.
        class_names: A class names list.
        model_size:The input size of the model.
    Returns:
        None.
    """
    cls = 0
    boxes_dict = boxes_dicts[0]
    resize_factor = (frame_size[0] / model_size[1], frame_size[1] / model_size[0])
    colors = (np.array(color_palette("hls", 80)) * 255).astype(np.uint8)
    boxes = boxes_dict[cls]
    color = colors[cls]
    color = tuple([int(x) for x in color])
    rects = []
    if np.size(boxes) != 0:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        trackers = []
        for box in boxes:
            xy = box[:4]
            xy = [int(xy[i] * resize_factor[i % 2]) for i in range(4)]
            # construct a dlib rectangle object from the bounding
            # box coordinates and then start the dlib correlation tracker
            tracker = dlib.correlation_tracker()
            rect = dlib.rectangle(int(xy[0]), int(xy[1]), int(xy[2]), int(xy[3]))
            tracker.start_track(rgb, rect)
            # add the tracker to our list of trackers so we can utilize it during skip frames
            trackers.append(tracker)
        for tracker in trackers:
            # update the tracker and grab the updated position
            tracker.update(rgb)
            pos = tracker.get_position()
            # unpack the position object
            startX = int(pos.left())
            startY = int(pos.top())
            endX = int(pos.right())
            endY = int(pos.bottom())
            # add the bounding box coordinates to the rectangles list
            rects.append((startX, startY, endX, endY))
    objects = ct.update(rects)
    if objects.__len__() == 0:
        count = -1
    else:
        count = max(objects.keys()) + 1
    people_number = max(people_number, count)
        # print(count + 1)
    cv2.putText(frame, "Count: " + str(people_number), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    # loop over the tracked objects
    for (objectID, centroid) in objects.items():
        # check to see if a trackable object exists for the current
        # object ID
        to = trackableObjects.get(objectID, None)
        # if there is no existing trackable object, create one
        if to is None:
            to = TrackableObject(objectID, centroid)
        # otherwise, there is a trackable object so we can utilize it
        # to determine direction
        else:
            to.centroids.append(centroid)
            # check to see if the object has been counted or not
            if not to.counted:
                to.counted = True
        # store the trackable object in our dictionary
        trackableObjects[objectID] = to
        # draw both the ID of the object and the centroid of the
        # object on the output frame
        text = "ID {}".format(objectID)
        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

        cv2.rectangle(frame, (centroid[2], centroid[3]), (centroid[4], centroid[5]), color[::-1], 2)
        (text_width, text_height), baseline = cv2.getTextSize(text,
                                                              cv2.FONT_HERSHEY_SIMPLEX,
                                                              0.75, 1)
        cv2.rectangle(frame, (centroid[2], centroid[3]),
                      (centroid[2] + text_width, centroid[3] - text_height - baseline),
                      color[::-1], thickness=cv2.FILLED)
        cv2.putText(frame, text, (centroid[2], centroid[3] - baseline),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 1)

    return people_number

