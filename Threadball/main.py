import time
import serial
import random

# from gpiozero import Motor, Servo
# import RPi.GPIO as GPIO

# 初始化串口通信
ser = serial.Serial('/dev/ttyUSB0', 115200)

# 假设我们有合适的库来控制这些硬件
# mpu = MPU6050()
# motor_FR = Motor(forward=1, backward=2)
# motor_BR = Motor(forward=3, backward=4)
# motor_BL = Motor(forward=5, backward=6)
# motor_FL = Motor(forward=7, backward=8)
# servoback = Servo(17)  # 使用合适的GPIO引脚
# servofront = Servo(18) # 使用合适的GPIO引脚

# PID参数
Kp = 1.0  # 比例增益，可以根据实际情况调整

# 目标角度
targetAngle = 0.0
find_dog = 0
mood_enable = 0
ball_find_enable = 0
catch_ball = 0
class_id = 0
x, y, width, height = 0.00, 0.00, 0.00, 0.00


def calculateRotationAngle(x):
    centerX = 400.0
    angle = (x - centerX) * 45.0 / centerX  # 最大旋转角度设为45度
    return angle


def timeCalculate(angle):
    timePerAngle = 7.3
    sumtime = 7.3 * abs(angle)
    return sumtime


def forwardTime(height):
    dis = 9500 / height
    time = dis / 15 * 250
    return time


def goToDistance(time_duration):
    ser.write(b'w')
    time.sleep(time_duration)
    ser.write(b'p')


def rotateToAngle(angle):
    print("Enter rotateToAngle")
    time_duration = timeCalculate(angle)
    print(f"total time: {time_duration}")
    if angle > 0: #turn right
        ser.write(b'd')
        time.sleep(time_duration)
        ser.write(b'p')
    elif angle < 0:
        ser.write(b'a')
        time.sleep(time_duration)
        ser.write(b'p')


def throwBall():
    randomValue = random.randint(0, 90)
    randomAngle = randomValue - 45
    rotateToAngle(randomAngle)
    openServo()


def fetchBall():
    while True:
        if ser.in_waiting > 0:
            data_str_x = ser.readline().decode('utf-8').strip()
            x = float(data_str_x)
            data_str_y = ser.readline().decode('utf-8').strip()
            y = float(data_str_y)
            data_str_width = ser.readline().decode('utf-8').strip()
            width = float(data_str_width)
            data_str_height = ser.readline().decode('utf-8').strip()
            height = float(data_str_height)

            print(f"ball data: {x} {y} {width} {height}")

            while ser.in_waiting > 0:
                ser.read()

            shutServo()
            time.sleep(3)
            break
        police()


def openServo():
    ser.write(b'w')#go straight a little time
    time.sleep(0.12)
    ser.write(b'p')
    ser.write(b'o')#open the gate

def shutServo():
    ser.write(b'h')#shut the gate

def main_loop():
    global find_dog, mood_enable, ball_find_enable, catch_ball, x, y, width, height, class_id

    while True:
        if not find_dog:
            ser.write(b'r')

            #what time is it to stop?
            #ser.write(b'p')
            while True:

                    angle = calculateRotationAngle(x)
                    print(f"Target angle: {angle}")
                    rotateToAngle(angle)
                    time.sleep(0.5)

                    time_duration = forwardTime(height)
                    goToDistance(time_duration)

                    mood_enable = 1


        print(f"mood_enable: {mood_enable}")
        if mood_enable:
            while True:
                if ser.in_waiting > 0:
                    class_id = int(ser.readline().decode('utf-8').strip())
                    ser.reset_input_buffer()
                    if class_id == 0:  # happy
                        for _ in range(2):
                            throwBall()
                            fetchBall()

                        ball_find_enable = 1
                        mood_enable = 0
                        break
                    elif class_id == 1:  # sad
                        time.sleep(3)
                        mood_enable = 0
                        break
                    elif class_id == 2:  # sleepy
                        time.sleep(3)
                        mood_enable = 0
                        break

        find_dog = 0
        mood_enable = 0
        ball_find_enable = 0
        catch_ball = 0

if __name__ == "__main__":
    main_loop()

