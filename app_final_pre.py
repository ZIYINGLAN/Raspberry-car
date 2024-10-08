#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.
import io
import logging
import socketserver
from http import server
from threading import Condition
import threading
from datetime import datetime
import cv2
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

import os
import serial
from PIL import Image
import paho.mqtt.client as mqtt
import numpy as np
import random
import sys

import pygame

display_enable = 1

angle_ball = 40
find_the_ball = 0

# 创建存储 delta_x 和 delta_y 的临时变量
temp_delta_x = 0
temp_delta_y = 0

signal = 0 
# 0: object_detection
# 1: mood_classification
# 2: ball_detection
ser = serial.Serial('/dev/ttyACM0',115200,timeout=1)
ser.write('i'.encode('utf-8'))
# ser.write('k'.encode('utf-8'))

def calculateRotationAngle(position):
    centerX = 400.0
    
    angle = (position - centerX) * 45.0 / centerX 
    return angle

def timeCalculate(angle):
    timePerAngle = 10
    sumtime = 10 * abs(angle)
    return sumtime

def forwardTime(height):
    # dis = 9500 / height
    dis = 5000 / height
    time = dis / 15 * 250
    return time

def goToDistance(time_duration):
    ser.write('w'.encode('utf-8'))
    time.sleep(time_duration/1000)
    ser.write('p'.encode('utf-8'))

def rotateToAngle(angle):
    print("Enter rotateToAngle")
    time_duration = timeCalculate(angle)
    print(f"total time: {time_duration}")
    if angle > 0: #turn right
        ser.write('d'.encode('utf-8'))
        time.sleep(time_duration/1000)
        ser.write('p'.encode('utf-8'))
    elif angle < 0:
        ser.write('a'.encode('utf-8'))
        time.sleep(time_duration/1000)
        ser.write('p'.encode('utf-8'))

def throwBall():
    try:
        # randomValue = random.uniform(0, 90)
        # randomAngle = randomValue - 45
        # rotateToAngle(randomAngle*10)
        rotateToAngle(120)
        openServo()
    except Exception as e:
        print(f"Error throwing the ball. E:{str(e)}")
    
def findBall():
    return None
    
def fetchBall():
    shutServo()
    
def openServo():
    ser.write('t'.encode('utf-8'))

def shutServo():
    ser.write('h'.encode('utf-8')) # shut the gate

def read_from_serial():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            if line:
                try:
                    parts = line.split(':')
                    if len(parts) == 2:
                        label, value = parts
                        if label.strip() == "Received data":
                            print(f"Received data: {value}")
                        elif label.strip() == "Target angle":
                            print(f"Target angle: {value}")
                        elif label.strip() == "total time":
                            print(f"total time: {value}")
                        elif label.strip() == "picked_up":
                            signal = 0
                        elif label.strip() == "input":
                            print((f"input: {value}"))
                        elif label.strip() == "camera":
                            print(f"camera: init")
                except ValueError as e:
                    print(f"Error parsing line: {line}, Error: {e}")

serial_thread = threading.Thread(target=read_from_serial)
serial_thread.daemon = True
serial_thread.start()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected.")
        client.subscribe("Group6/IMAGE/predict")  
    else:
        print("Failed to connect. Error code: ", rc)
        
def on_message(client, userdata, msg):
    global signal
    global display_enable
    global find_the_ball
    global angle_ball
    try:
        if signal == 0:
            print("Received dog object information.")
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
            
            if class_id != -1:
                if width * height <= 120000: 
                    angle = calculateRotationAngle(center_x)
                    print(f"Target angle: {angle}")
                    rotateToAngle(angle*0.5)
                    time.sleep(0.5)

                    time_duration = forwardTime(height)
                    goToDistance(time_duration*0.8)
                    
                elif width * height > 120000 and width * height < 384000:
                    signal = 1

            elif class_id == -1:
                rotateToAngle(20)

        elif signal == 1:       
            print("Received mood classification information.")
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
            if class_id != -1 and display_enable == 1:
                display_enable = 0
                if class_id == 0: # happy
                    for _ in range(2):
                        throwBall()
                        ser.write('k'.encode('utf-8'))
                        ser.write('o'.encode('utf-8'))
                        while True:
                            call_findball()
                            if find_the_ball == 1:
                                find_the_ball = 0
                                angle_ball = 40
                                break
                        ser.write('i'.encode('utf-8'))
                        fetchBall()
                        time.sleep(1.5)
                        # time.sleep(20)
                        print("Successfully catch the ball!!!!!") 
                    display_enable = 1
                elif class_id == 1: # sad
                    pygame.mixer.init()
                    pygame.mixer.music.load("/home/yizhangzhi/Downloads/sad.mp3")
                    pygame.mixer.music.play()
                    clock = pygame.time.Clock()
                    while pygame.mixer.music.get_busy():
                        clock.tick(10)
                    pygame.quit()
                    display_enable = 1
                elif class_id == 2: # sleepy
                    pygame.mixer.init()
                    pygame.mixer.music.load("/home/yizhangzhi/Downloads/sleepy.mp3")
                    pygame.mixer.music.play()
                    clock = pygame.time.Clock()
                    while pygame.mixer.music.get_busy():
                        clock.tick(10)
                    pygame.quit()
                    display_enable = 1
            elif class_id == -1 and display_enable == 1: # not processing display now
                signal = 0
            else:
                do_nothing = 0
        
        # elif signal == 2:
        #     print("Received ball object information.")
        #     payload = json.loads(msg.payload)
        #     class_id = int(payload.get('class_id'))
        #     center_x = float(payload.get('center_x'))
        #     center_y = float(payload.get('center_y'))
        #     width = float(payload.get('width'))
        #     height = float(payload.get('height'))
        #     print(class_id)
        #     print(center_x)
        #     print(center_y)
        #     print(width)
        #     print(height)
        #     # x : 0 ~ 800
        #     # y : 0 ~ 480
        #     # center : (400, 240)  
        #     data_str_x = f"{center_x}\n"
        #     ser.write(data_str_x.encode('utf-8'))
        #     data_str_y = f"{center_y}\n"
        #     ser.write(data_str_y.encode('utf-8'))
        #     data_str_width = f"{width}\n"
        #     ser.write(data_str_width.encode('utf-8'))
        #     data_str_height = f"{height}\n"
        #     ser.write(data_str_height.encode('utf-8'))
        
    except Exception as e:
        print(f"Error handling message from server.")
    

def setup(hostname):
    client = mqtt.Client()
    client.username_pw_set("XYC", "20030601")
    client.on_message = on_message
    client.on_connect = on_connect
    client.connect(hostname)
    client.loop_start()
    return client

SAMPLE_PATH = 'captured_images'

def send_image(client, filename):
    global signal
    global display_enable
    try:
        filepath = os.path.join(SAMPLE_PATH, filename)
        with open(filepath, "rb") as f:
            img_bytes = f.read()
        
        payload = {
            "signal": signal,
            "filename": filename,
            "data": img_bytes.decode('latin1')
        }
        if display_enable == 1:
            client.publish("Group6/IMAGE/classify", json.dumps(payload), qos=1)
            print(f"Image {filename} sent successfully.")
        elif display_enable == 0:
            print(f"Image busy to send.")
    
    except Exception as e:
        print(f"Error sending image {filename}: {str(e)}")
    
client=setup("192.168.137.35")
print("Setup Done.")

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
# ser = serial.Serial('/dev/ttyUSB0',9600,timeout=1)

# 获取摄像头分辨率
width = 800
height = 480

# 蓝色小球的 HSV 颜色范围
lower_blue = np.array([100, 200, 70])
upper_blue = np.array([140, 255, 255])

# 计算屏幕中心点
center_x, center_y = width // 2, height // 2

def calculate_angle_and_distance(delta_x, delta_y):
    angle = np.arctan2(delta_y, delta_x) * (180.0 / np.pi)
    distance = np.sqrt(delta_x**2 + delta_y**2)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_auto_capture()
    
    def do_GET(self):
        global output
        global temp_delta_x
        global temp_delta_y
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
                    # 捕获一帧图像
                    frame = picam2.capture_array()
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  
                    # 将 BGR 图像转换为 HSV 图像
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    # 创建一个掩膜，只保留蓝色区域
                    mask = cv2.inRange(hsv, lower_blue, upper_blue)
                    # 寻找蓝色区域的轮廓
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        # 选择最大轮廓
                        c = max(contours, key=cv2.contourArea)
                        # 计算轮廓的质心
                        M = cv2.moments(c)
                        if M['m00'] != 0:
                            cX = int(M['m10'] / M['m00'])
                            cY = int(M['m01'] / M['m00'])
                            # 计算x和y的差值
                            delta_x = cX - center_x
                            delta_y = cY - center_y
                            # print("Sending cur_x: ", delta_x)
                            # print("Sending cur_y: ", delta_y)
                            # data_str = f"{delta_x} {delta_y}"
                            # ser.write(data_str.encode('utf-8'))
                            temp_delta_x = delta_x
                            temp_delta_y = delta_y
                            # 计算角度和距离
                            angle, distance = calculate_angle_and_distance(delta_x, delta_y)
                            # 在图像上绘制质心
                            cv2.drawContours(frame, [c], -1, (255, 0, 0), 2)
                            cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
                            cv2.line(frame, (center_x, center_y), (cX, cY), (0, 255, 0), 1)
                            # 显示角度、距离和差值
                            cv2.putText(frame, f"Angle: {angle:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            # cv2.putText(frame, f"Distance: {distance:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.putText(frame, f"Delta X: {delta_x}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.putText(frame, f"Delta Y: {float(0-delta_y)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        temp_delta_x = -1000
                        temp_delta_y = -1000
                            
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if not ret:
                        continue
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/take_picture':
            # # cut current frame
            # frame = picam2.capture_array()
            # if frame is not None:
            #     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            #     filename = f'captured_image_{timestamp}.jpg'
            #     filepath = os.path.join(SAMPLE_PATH, filename)
            #     if not os.path.exists(SAMPLE_PATH):
            #         os.makedirs(SAMPLE_PATH)
            #     bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            #     cv2.imwrite(filepath, bgr_frame)
                
            #     with open(filepath, 'rb') as f:
            #         send_image(client, filename)
            self.take_picture()
        else:
            self.send_error(404)
            self.end_headers()
    
    def take_picture(self):
        frame = picam2.capture_array()
        if frame is not None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'captured_image_{timestamp}.jpg'
            filepath = os.path.join(SAMPLE_PATH, filename)
            if not os.path.exists(SAMPLE_PATH):
                os.makedirs(SAMPLE_PATH)
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, bgr_frame)

            with open(filepath, 'rb') as f:
                send_image(client, filename)
    
    def start_auto_capture(self):
        self.auto_capture_timer = threading.Timer(3, self.auto_capture)
        self.auto_capture_timer.start()
    
    def auto_capture(self):
        self.take_picture() 
        self.auto_capture_timer = threading.Timer(8, self.auto_capture)
        self.auto_capture_timer.start()
    

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

picam2 = Picamera2() # argument: switch camera
picam2.configure(picam2.create_video_configuration(main={"size": (800, 480)}))
output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

def rotate(cur_x):
    print("detect the ball, rotating... ")
    if cur_x > 60: #turn right
        ser.write('d'.encode('utf-8'))
        time.sleep(0.07)
        ser.write('p'.encode('utf-8'))
    elif cur_x < -60: #turn left
        ser.write('a'.encode('utf-8'))
        time.sleep(0.07)
        ser.write('p'.encode('utf-8'))
    else:
        ser.write('p'.encode('utf-8'))
        print("rotation is finishing... ")

def straight(cur_y):
    print("detect the ball, go straighting... ")
    if cur_y < 200:
        act_y = 250 - cur_y
        ser.write('w'.encode('utf-8'))
        time.sleep(0.15*act_y/400)
        ser.write('p'.encode('utf-8'))
    else:
        ser.write('p'.encode('utf-8'))
        print("Going straight is finishing... ")

def findball(cur_x, cur_y):
    """Function to find the ball and adjust car movement"""
    global angle_ball
    global find_the_ball
    print(f"cur_x: {cur_x}, cur_y: {cur_y}, angle: {angle_ball}")
    if cur_x == -1000 and cur_y == -1000:
        print("not find the ball")
        ser.write('d'.encode('utf-8'))
        time.sleep(0.2)
        ser.write('p'.encode('utf-8'))
    else:
        if angle_ball > 0:
            if 80 > cur_x and cur_x > -80 and cur_y > 120:
                print(f"angle({angle_ball}) catch the ball.")
                ser.write('p'.encode('utf-8'))
                time.sleep(0.2)
                print(f"lower the angle")
                ser.write('c'.encode('utf-8'))
                angle_ball -= 10
                # straight(cur_y)
            else:
                ser.write('p'.encode('utf-8'))
                rotate(cur_x)
                time.sleep(0.2)
                straight(cur_y)
        else:
            if 80 > cur_x and cur_x > -80 and cur_y > -100:
                print(f"Already find the ball")
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
                find_the_ball = 1
            else:
                print("Sending 'p' command")
                ser.write('p'.encode('utf-8'))
                rotate(cur_x)
                time.sleep(0.2)
                straight(cur_y*0.3)

def call_findball():
    global temp_delta_x
    global temp_delta_y
    findball(temp_delta_x, temp_delta_y)
    time.sleep(0.6)  
        
try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
