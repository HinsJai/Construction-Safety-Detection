from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import os
import sys
from math import ceil
from typing import Any
import numpy as np
from ultralytics import YOLO
from enum import Enum

# from math import ceil

sys.path.extend([".."])
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploaded"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"mp4", "jpg", "jpeg", "png"}

current_source = "camera"  # 'camera' or 'file'
model = YOLO("../model/best_100.pt")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

Label = Enum(
    "label",
    [
        "Hardhat",
        "Mask",
        "No Hardhat",
        "No Mask",
        "No Safety Vest",
        "Person",
        "Safety Cone",
        "Safety Vest",
        "Machinery",
        "Vehicle",
    ],
)


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


def allowed_file(filename) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file() -> object:
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        global current_source
        current_source = filepath
        return (
            jsonify({"message": "File uploaded successfully", "filename": filename}),
            200,
        )
    else:
        return jsonify({"error": "File type not allowed"}), 400


@app.route("/frame_feed")
def frame_feed() -> Response:
    def generate() -> Any:
        global current_source
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if current_source == "camera":
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                if not (result := model.predict(frame, verbose=False)):
                    return None

                for detection in result[0].boxes:
                    if ceil((detection.conf[0] * 100)) > 0.5 * 100:
                        x1 = int(detection.xyxy[0][0])
                        y1 = int(detection.xyxy[0][1])
                        x2 = int(detection.xyxy[0][2])
                        y2 = int(detection.xyxy[0][3])
                        label = Label(int(detection.cls[0]) + 1).name
                        conf = ceil((detection.conf[0] * 100))

                        # background_color = (255, 69, 0)
                        text_color = (255, 255, 255)
                        box_color = get_box_color(int(detection.cls[0]))

                        # Draw the rectangle background for text
                        text = f"{label} {conf:.2f}"
                        (text_width, text_height), _ = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2
                        )
                        cv2.rectangle(
                            frame,
                            (x1, y1 - text_height - 15),
                            (x1 + text_width, y1),
                            box_color,
                            -1,
                        )

                        # Draw the text on top of the rectangle
                        cv2.putText(
                            frame,
                            text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.75,
                            text_color,
                            2,
                        )

                        # Draw the bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                ret, buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    print("Failed to encode image")
                    continue
                frame = buffer.tobytes()

                yield (
                    b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
        else:
            frame = cv2.imread(current_source)
            if frame is None:
                print("Failed to read image from file")
                return

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/switch_to_camera", methods=["POST"])
def switch_to_camera() -> object:
    global current_source
    current_source = "camera"
    return jsonify({"message": "Switched to camera"}), 200


@app.route("/upload/<filename>")
def uploaded_file(filename) -> str:
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
