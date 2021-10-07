import RPi.GPIO as GPIO
import time
from time import sleep
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import json

def customShadowCallback_Update(payload, responseStatus, token):
    # Display status and data from update request
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")

    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("Reported state: " + str(payloadDict["state"]["reported"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    TRIG = 7
    ECHO = 11
    GREEN = 16
    RED = 15
    maxTime = 0.04
    GPIO.setup(GREEN, GPIO.OUT)
    GPIO.setup(RED, GPIO.OUT)
    # Init AWSIoTMQTTShadowClient
    myAWSIoTMQTTShadowClient = None
    myShadowClient = AWSIoTMQTTShadowClient("AWS_IOT_DEVICE_NAME")
    myShadowClient.configureEndpoint("AWS_IOT_ENDPOINT", 8883)
    myShadowClient.configureCredentials("AWS_IOT_CA_CRT",
      "AWS_IOT_PRIVATE_KEY",
      "AWS_IOT_CERT_PEM")
    myShadowClient.configureConnectDisconnectTimeout(10) # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5) # 5 sec
    myShadowClient.connect()
    myDeviceShadow = myShadowClient.createShadowHandlerWithName("AWS_IOT_DEVICE_NAME", True)

    while True:
      GPIO.setup(TRIG,GPIO.OUT)
      GPIO.setup(ECHO,GPIO.IN)
      GPIO.output(TRIG,False)
      time.sleep(0.01)
      GPIO.output(TRIG,True)
      time.sleep(0.00001)
      GPIO.output(TRIG,False)
      pulse_start = time.time()
      timeout = pulse_start + maxTime
      while GPIO.input(ECHO) == 0 and pulse_start < timeout:
          pulse_start = time.time()

      pulse_end = time.time()
      timeout = pulse_end + maxTime
      while GPIO.input(ECHO) == 1 and pulse_end < timeout:
          pulse_end = time.time()
      pulse_duration = pulse_end - pulse_start
      distance = pulse_duration * 17000
      distance = round(distance, 2)

      if float(distance) < float(8):
        GPIO.output(GREEN, False)
        GPIO.output(RED, True)
        payload = {"state":{"reported": {"FREE": False, "DISTANCE": distance}}}
        myDeviceShadow.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)
      else:
        GPIO.output(GREEN, True)
        GPIO.output(RED, False)
        payload = {"state":{"reported": {"FREE": True, "DISTANCE": distance}}}
        myDeviceShadow.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)
      sleep(0.5)

      print(distance)
except Exception as e:
    print(str(e))
    GPIO.cleanup()