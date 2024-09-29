#!/usr/bin/python3

import io
import logging
import socketserver
from http import server
from threading import Condition
from datetime import datetime
import cv2
import json
import time
import threading
from multiprocessing import Process, Value, Array
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
import os
import serial
from PIL import Image
import paho.mqtt.client as mqtt
import numpy as np

# Initialize serial communication with Arduino
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)


# MQTT connection callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected.")
        client.subscribe("Group6/IMAGE/predict")
    else:
        print("Failed to connect. Error code: ", rc)


# MQTT message callback
def on_message(client, userdata, msg):
    try:
        print("Received object information.")
        payload = json.loads(msg.payload)
        class_id = int(payload.get('class_id'))
        center_x = float(payload.get('center_x'))
        center_y = float(payload.get('center_y'))
        width = float(payload.get('width'))
        height = float(payload.get('height'))
        print(class_id)
        print(center_x)
        print(center_y)
        print(width)
        print(height)
    except Exception as e:
        print(f"Error handling message from server.")


# HTML page for video stream
PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
<style>
body {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    text-align: center;
}
.center {
    max-width: 80%;
    padding: 20px;
}
</style>
</head>
<body>
<div class="center">
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img id="stream" src="stream.mjpg" width="800" height="480" />
<br/>
<button onclick="takePicture()">Take Picture</button>
</div>

<script>
function takePicture() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/take_picture", true);
    xhr.send();
}
</script>
</body>
</html>
"""

# Frame dimensions
width = 800
height = 480

# HSV color range for detecting blue ball
lower_blue = np.array([100, 200, 70])
upper_blue = np.array([140, 255, 255])

# Calculate screen center
center_x, center_y = width // 2, height // 2


def calculate_angle_and_distance(delta_x, delta_y):
    angle = np.arctan2(delta_y, delta_x) * (180.0 / np.pi)
    distance = np.sqrt(delta_x ** 2 + delta_y ** 2)
    return angle, distance


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global output
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def rotate(cur_x):
    """Function to rotate the car towards the ball"""
    print("detect the ball, rotating... ")
    if cur_x > 30:  # turn left
        print("Sending 'a' command")
        ser.write('a'.encode('utf-8'))
    elif cur_x < -30:  # turn right
        print("Sending 'd' command")
        ser.write('d'.encode('utf-8'))
    else:
        print("Sending 'p' command")
        ser.write('p'.encode('utf-8'))
        print("rotation is finishing... ")


def straight(cur_y):
    """Function to move the car straight towards the ball"""
    print("detect the ball, go straighting... ")
    if cur_y < 200:
        print("Sending 'w' command")
        ser.write('w'.encode('utf-8'))
    else:
        print("Sending 'p' command")
        ser.write('p'.encode('utf-8'))
        print("Going straight is finishing... ")


def findball(cur_x, cur_y):
    """Function to find the ball and adjust car movement"""
    global angle
    global detectBall
    print(f"cur_x: {cur_x}, cur_y: {cur_y}, angle:  detectBall: {detectBall}")
    if detectBall == 0:
        print("Sending 'r' command to rotate for ball detection")
        ser.write('r'.encode('utf-8'))
        time.sleep(0.1)
        print("Sending 'p' command to pause")
        ser.write('p'.encode('utf-8'))
    else:
        detectBall = 1
        if angle > 0:
            if 30 > cur_x > -30 and cur_y > 200:
                print(f"{angle} find the ball")
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
                time.sleep(0.1)
                print("Sending 'c' command to capture")
                ser.write('c'.encode('utf-8'))
                angle -= 10
            else:
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
                rotate(cur_x)
                time.sleep(0.1)
                straight(cur_y)
        else:
            if 30 > cur_x > -30 and cur_y > 100:
                print(f"{angle} find the ball")
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
            else:
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
                rotate(cur_x)
                time.sleep(0.1)
                straight(cur_y)


def call_findball(delta_x, delta_y):
    """Process function to periodically call findball"""
    while True:
        cur_x = delta_x.value
        cur_y = delta_y.value
        findball(cur_x, cur_y)
        time.sleep(0.3)


if __name__ == '__main__':
    # Shared memory for delta_x and delta_y
    delta_x = Value('d', 0.0)
    delta_y = Value('d', 0.0)
    detectBall = 0
    angle = 40

    # Start the findball process
    findball_process = Process(target=call_findball, args=(delta_x, delta_y))
    findball_process.start()

    # Initialize the camera
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (800, 480)}))
    output = StreamingOutput()
    picam2.start_recording(MJPEGEncoder(), FileOutput(output))

    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()

        while True:
            # Read frame from the camera
            frame = picam2.capture_array()
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Mask for blue color
            mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Find the largest contour
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                (x, y), radius = cv2.minEnclosingCircle(largest_contour)
                if radius > 10:
                    delta_x.value = x - center_x
                    delta_y.value = center_y - y

            time.sleep(0.03)
    finally:
        picam2.stop_recording()
        findball_process.terminate()
