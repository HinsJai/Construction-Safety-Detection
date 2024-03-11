from flask import Flask, request, jsonify, Response, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import os
import sys
import time

from collections import deque
from math import ceil
from typing import Any
import numpy as np
from ultralytics import YOLO
import concurrent.futures as cf
from vidgear.gears import CamGear
from collections import Counter


sys.path.extend([".."])

app = Flask(__name__)
CORS(app)

# UPLOAD_FOLDER = "uploaded"
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# ALLOWED_EXTENSIONS = {"mp4", "jpg", "jpeg", "png"}
# os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# CURRENT_SOURCE = "camera"  # 'camera' or 'file'
VIDEO_SOURCE = 0  # Default camera
youtube = "http://www.youtube.com/watch?v=q0kPBRIPm6o"  # Default youtube live stream

cap = cv2.VideoCapture(VIDEO_SOURCE)
youtube_cap = CamGear(source=youtube, stream_mode=True, logging=True).start()

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
resize_width = 1280
resize_height = 720
if frame_width > 0:
    resize_height = int((resize_width / frame_width) * frame_height)

model = YOLO("../model/best_100.pt")


def predict_and_detect(model, img, conf=0.5) -> tuple:

    # img = cv2.resize(img, (resize_width, resize_height))

    img = cv2.resize(img, (resize_width, resize_height))

    results = model.predict(img, conf=conf, verbose=False)
    names = results[0].names
    class_detections_values = []
    for k, v in names.items():
        class_detections_values.append(results[0].boxes.cls.tolist().count(k))
    # create dictionary of objects detected per class
    classes_detected = dict(zip(names.values(), class_detections_values))

    if not results:
        results = []

    for result in results:
        for box in result.boxes:
            x1 = int(box.xyxy[0][0])
            y1 = int(box.xyxy[0][1])
            x2 = int(box.xyxy[0][2])
            y2 = int(box.xyxy[0][3])
            label = result.names[int(box.cls[0])]
            conf = ceil((box.conf[0] * 100))

            text_color = (255, 255, 255)
            box_color = get_box_color(int(box.cls[0]))

            # Draw the rectangle background for text
            text = f"{label} {conf:.2f}"
            (text_width, text_height), _ = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2
            )
            cv2.rectangle(
                img,
                (x1, y1 - text_height - 15),
                (x1 + text_width, y1),
                box_color,
                -1,
            )

            # Draw the text on top of the rectangle
            cv2.putText(
                img,
                text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                text_color,
                2,
            )
            cv2.rectangle(img, (10, 60), (10 + 300, 20), (0, 0, 0), -1)

            cv2.putText(
                img,
                f"Total Person: {classes_detected['Person']}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

            # Draw the bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)
    return img, results


def process_frame(frame) -> np.ndarray:
    result_frame, _ = predict_and_detect(model, frame)
    return result_frame


# BRG color
def get_box_color(index: int) -> tuple:
    match index:
        case 0:
            return (0, 255, 0)  # Green
        case 1:
            return (0, 255, 0)  # Green
        case 2:
            return (0, 0, 255)  # Red
        case 3:
            return (0, 0, 255)  # Red
        case 4:
            return (0, 0, 255)  # Red
        case 7:
            return (0, 255, 0)  # Green
        case _:
            return (255, 0, 0)  # Blue


# def allowed_file(filename) -> bool:
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/image_predict", methods=["POST"])
def predict_image() -> object:
    if "image" not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files["image"]
    if file:
        # Read the image file in a NumPy array format
        npimg = np.fromfile(file, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # Process the image directly with the model
        result_frame = process_frame(img)

        # Convert the image with predictions back to bytes and send as a response
        _, buffer = cv2.imencode(".jpg", result_frame)
        return Response(buffer.tobytes(), mimetype="image/jpeg")

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/frame_feed")
def frame_feed() -> Response:
    def generate() -> Any:

        skip_frames = 2  # Number of frames to skip before processing the next one
        frame_count = 0
        # if CURRENT_SOURCE == "camera":
        with cf.ThreadPoolExecutor() as executor:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count = 1 + frame_count
                if frame_count % skip_frames != 0:
                    continue  # Skip this frame

                future = executor.submit(process_frame, frame)
                result_frame = future.result()

                ret, buffer = cv2.imencode(".jpg", result_frame)
                encoded_frame = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + encoded_frame + b"\r\n"
                )
                time.sleep(0.01)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/youtube_feed")
def youtube_feed() -> Response:
    def generate() -> Any:

        skip_frames = 2
        frame_count = 0

        with cf.ThreadPoolExecutor() as executor:
            while True:
                frame = youtube_cap.read()
                if frame is None:
                    break

                frame_count = 1 + frame_count
                if frame_count % skip_frames != 0:
                    continue  # Skip this frame

                future = executor.submit(process_frame, frame)
                result_frame = future.result()

                ret, buffer = cv2.imencode(".jpg", result_frame)
                encoded_frame = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + encoded_frame + b"\r\n"
                )
                time.sleep(0.01)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/switch_to_camera", methods=["POST"])
def switch_to_camera() -> Response:
    global CURRENT_SOURCE
    # global cap
    # cap = cv2.VideoCapture(VIDEO_SOURCE)
    CURRENT_SOURCE = "camera"
    return jsonify({"message": "Switched to camera"}), 200


@app.route("/switch_to_youtube", methods=["POST"])
def switch_to_youtube() -> Response:
    global CURRENT_SOURCE
    global youtube_cap
    global youtube
    CURRENT_SOURCE = "youtube"
    youtube_url = request.json["youtubeUrl"]
    if youtube_url == "":
        youtube_url = "http://www.youtube.com/watch?v=q0kPBRIPm6o"

    youtube_cap = CamGear(source=youtube_url, stream_mode=True, logging=False).start()
    return jsonify({"message": "Switched to youtube"}), 200


@app.route("/switch_to_image", methods=["POST"])
def switch_to_image() -> Response:
    global CURRENT_SOURCE
    CURRENT_SOURCE = "image"
    return jsonify({"message": "Switched to image"}), 200


if __name__ == "__main__":
    app.run(debug=True)
