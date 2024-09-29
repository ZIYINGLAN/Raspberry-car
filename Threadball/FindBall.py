import serial
import time

ser = serial.Serial('COM3', 115200)  # 请根据实际情况更改端口号和波特率

cur_x = 0.0
cur_y = 0.0
width = 0.0
height = 0.0

detectBall = 0

def rotate(cur_x):
    print("detect the ball, rotating... ")
    if cur_x > 30: #turn left
        ser.write('a'.encode('utf-8'))
    elif cur_x < -30: #turn right
        ser.write('d'.encode('utf-8'))
    else:
        ser.write('p'.encode('utf-8'))
        print("rotation is finishing... ")

def straight(cur_y):
    print("detect the ball, go straighting... ")
    if cur_y < 200:
        ser.write('w'.encode('utf-8'))
    else:
        ser.write('p'.encode('utf-8'))
        print("Going straight is finishing... ")


if __name__ == "__main__":
    global cur_x, cur_y, width, height
    angle=40
    if detectBall == 0: #无法识别到球
        ser.write('r'.encode('utf-8'))
        time.sleep(0.1) #设置findball频率为0.2s/time
        ser.write('p'.encode('utf-8'))
    else: #识别到球
        detectBall = 1
        #前四次找
            if angle > 0:
                if 30 > cur_x > -30 and cur_y > 200:
                    print(f"{angle} find the ball")
                    ser.write('p'.encode('utf-8'))
                    time.sleep(0.1)
                    ser.write('c'.encode('utf-8'))
                    angle -= 10
                else:
                    ser.write('p'.encode('utf-8'))
                    rotate(cur_x)
                    time.sleep(0.1)
                    straight(cur_y)
        #最后一次找
            else:
                if 30 > cur_x > -30 and cur_y > 100:
                    print(f"{angle} find the ball")
                    ser.write('p'.encode('utf-8'))
                else:
                    ser.write('p'.encode('utf-8'))
                    rotate(cur_x)
                    time.sleep(0.1)
                    straight(cur_y)




