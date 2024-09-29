import io
import logging
import socketserver
from http import server
from threading import Condition, Thread
import cv2
import json
import time
import threading
import multiprocessing as mp
from multiprocessing import Queue, Process

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

import os
import serial
import numpy as np

# Serial port setup
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# MQTT setup (if needed)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected.")
        client.subscribe("Group6/IMAGE/predict")
    else:
        print("Failed to connect. Error code: ", rc)

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
        # x : 0 ~ 800
        # y : 0 ~ 480
        # center : (400, 240)

    except Exception as e:
        print(f"Error handling message from server.")
"""
def setup_mqtt(hostname):
    client = mqtt.Client()
    client.username_pw_set("XYC", "20030601")
    client.on_message = on_message
    client.on_connect = on_connect
    client.connect(hostname)
    client.loop_start()
    return client

client = setup_mqtt("192.168.137.196")
print("MQTT Setup Done.")
"""

# HTML page content
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

# Constants for video processing
width = 800
height = 480
lower_blue = np.array([100, 200, 70])
upper_blue = np.array([140, 255, 255])
center_x, center_y = width // 2, height // 2

# Shared queue for communication between processes
delta_queue = Queue(maxsize=100)


# Function to capture video stream and detect ball
def video_streaming(delta_queue):
    cap = cv2.VideoCapture(0)  # Assuming using the first camera

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to HSV and apply color threshold
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            (x, y), radius = cv2.minEnclosingCircle(largest_contour)
            if radius > 10:
                delta_x = x - center_x
                delta_y = center_y - y

                if not delta_queue.full():
                    delta_queue.put((delta_x, delta_y))

        time.sleep(0.03)

    cap.release()


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

# Function to control the motor based on ball position
def process_deltas(delta_queue):
    detectBall = 0
    angle = 40

    while True:
        if not delta_queue.empty():
            delta_x, delta_y = delta_queue.get()

            if detectBall == 0:
                print("Sending 'r' command to rotate for ball detection")
                ser.write('r'.encode('utf-8'))
                time.sleep(0.1)
                print("Sending 'p' command to pause")
                ser.write('p'.encode('utf-8'))
            else:
                detectBall = 1
                if angle > 0:
                    if 30 > delta_x > -30 and delta_y > 200:
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
                        rotate(delta_x)
                        time.sleep(0.1)
                        straight(delta_y)
                else:
                    if 30 > delta_x > -30 and delta_y > 100:
                        print(f"{angle} find the ball")
                        print("Sending 'p' command")
                        ser.write('p'.encode('utf-8'))
                    else:
                        print("Sending 'p' command")
                        ser.write('p'.encode('utf-8'))
                        rotate(delta_x)
                        time.sleep(0.1)
                        straight(delta_y)

        time.sleep(0.3)  # Control frequency


# Thread function to start HTTP server and handle requests
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


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# Start the video streaming process
video_process = Process(target=video_streaming, args=(delta_queue,))
video_process.start()

# Start the motor control process
motor_process = Thread(target=process_deltas, args=(delta_queue,))
motor_process.start()

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    video_process.terminate()
    video_process.join()

    motor_process.join()

    # Clean up
    server.shutdown()
    server.server_close()
    print("Server stopped.")
    ser.close()
