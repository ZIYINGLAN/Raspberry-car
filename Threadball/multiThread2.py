import cv2
import time
import multiprocessing as mp
from multiprocessing import Queue, Process
# 定义队列大小
QUEUE_SIZE = 10
delta_queue = Queue(maxsize=QUEUE_SIZE)

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

def video_streaming(delta_queue):
    cap = cv2.VideoCapture(0)  # 假设使用第一个摄像头
    center_x, center_y = 400, 240  # 假设图像中心在 (320, 240)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 转换为灰度图并进行轮廓检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

def process_deltas(delta_queue):
    while True:
        if not delta_queue.empty():
            delta_x, delta_y = delta_queue.get()
            # 处理delta_x和delta_y，例如控制小车
            findball(delta_x, delta_y)

        time.sleep(0.03)

if __name__ == "__main__":
    # 创建进程
    producer_process = Process(target=video_streaming, args=(delta_queue,))
    consumer_process = Process(target=process_deltas, args=(delta_queue,))

    # 启动进程
    producer_process.start()
    consumer_process.start()

    # 等待进程完成
    producer_process.join()
    consumer_process.join()


