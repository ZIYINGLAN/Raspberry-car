#include <AFMotor.h>
#include <Servo.h>

AF_DCMotor FrontRight(1); // 右前轮电机
AF_DCMotor BackRight(2); // 右后轮电机
AF_DCMotor BackLeft(3); // 左后轮电机
AF_DCMotor FrontLeft(4); // 左前轮电机
Servo servoback;//创建舵机对象
Servo servofront;
Servo servocap;
int servoangle = 40;

void setup() {
  FrontRight.setSpeed(150);
  BackRight.setSpeed(150);
  BackLeft.setSpeed(150);
  FrontLeft.setSpeed(150);
  Serial.begin(115200);
  servoback.attach(45, 500, 2500);
  servofront.attach(44, 500, 2500);
  servocap.attach(46, 500, 2500);
  servocap.write(40);
  servoback.write(25);//shut the back
  servofront.write(180); //shut the front
  
}

void loop() {
  if (Serial.available()) {

    char input = Serial.read();
    Serial.print("input: ");
    Serial.println(input);
    switch (input) {
      case 'w': 
        FrontRight.run(FORWARD);
        BackRight.run(FORWARD);
        BackLeft.run(BACKWARD);
        FrontLeft.run(BACKWARD);
        break;
      case 'f': 
        FrontRight.run(FORWARD);
        BackRight.run(FORWARD);
        BackLeft.run(BACKWARD);
        FrontLeft.run(BACKWARD);   
        break;
      case 's': 
        FrontRight.run(BACKWARD);
        BackRight.run(BACKWARD);
        BackLeft.run(FORWARD);
        FrontLeft.run(FORWARD);
        break;
      case 'b': // 后退两秒
        FrontRight.run(BACKWARD);
        BackRight.run(BACKWARD);
        BackLeft.run(FORWARD);
        FrontLeft.run(FORWARD);
        break;
      case 'a': // 左转
        FrontRight.setSpeed(200);
        BackRight.setSpeed(200);
        BackLeft.setSpeed(255);
        FrontLeft.setSpeed(255);
        FrontRight.run(BACKWARD);
        BackRight.run(BACKWARD);
        BackLeft.run(BACKWARD);
        FrontLeft.run(BACKWARD);
        break;
      case 'd': // 右转
        FrontRight.setSpeed(255);
        BackRight.setSpeed(255);
        BackLeft.setSpeed(200);
        FrontLeft.setSpeed(200);
        FrontRight.run(FORWARD);
        BackRight.run(FORWARD);
        BackLeft.run(FORWARD);
        FrontLeft.run(FORWARD);
        break;
      case 'z': // 左转90°
        FrontRight.run(BACKWARD);
        BackRight.run(BACKWARD);
        BackLeft.run(BACKWARD);
        FrontLeft.run(BACKWARD);
        break;
      case 'x': // 右转90°
        FrontRight.run(FORWARD);
        BackRight.run(FORWARD);
        BackLeft.run(FORWARD);
        FrontLeft.run(FORWARD);
        break;
      case 'p': // 停止
        FrontRight.run(RELEASE);
        BackRight.run(RELEASE);
        BackLeft.run(RELEASE);
        FrontLeft.run(RELEASE);
        break;
      case 'o':
        Serial.println("Open the gate");
        servofront.write(80); //open the front
        delay(100);
        servoback.write(115); //open the back
        delay(5);
        break;
      case 'h':
        Serial.println("shut the gate");
        servoback.write(25);//shut the back
        delay(100);
        servofront.write(180); //shut the front
        delay(5);
        break;
      case 'i': //initialize the camera
        servoangle = 40;
        servocap.write(servoangle);
        Serial.println("camera:initialize");
        break;
      case 'k': //camera settings in find the dog
        servoangle = 30;
        servocap.write(servoangle);
        Serial.println("camera:initialize");
        break;
      case 'c':
          Serial.println("turn the camera");//camera down
          // servocap.write(30); 
          if (servoangle > 0){
            servocap.write(servoangle);
            servoangle -= 10;
          }
        break;
      case 't':
        Serial.println("throw the ball");
        FrontRight.setSpeed(180);
        BackRight.setSpeed(180);
        BackLeft.setSpeed(180);
        FrontLeft.setSpeed(180);
        FrontRight.run(FORWARD);
        BackRight.run(FORWARD);
        BackLeft.run(BACKWARD);
        FrontLeft.run(BACKWARD);
        delay(500);
        servofront.write(80); //open the front
        delay(100);
        servoback.write(115); //open the back
        delay(100);
        FrontRight.setSpeed(100);
        BackRight.setSpeed(100);
        BackLeft.setSpeed(100);
        FrontLeft.setSpeed(100);

      default:
        break;
    }
  }
}
