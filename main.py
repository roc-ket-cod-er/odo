from secrets import passwd, ssid, userid, key
from umqtt.robust import MQTTClient
from machine import Pin, Timer, ADC, I2C
from customLCD import display
from _thread import allocate_lock, start_new_thread

import machine
import network
import time
import math
import sys
import dht
import random


lock = allocate_lock()

sensor = Pin(18, Pin.IN, Pin.PULL_UP)
run = Pin(19, Pin.IN, Pin.PULL_UP)
led = Pin("LED", Pin.OUT)

if run.value():
    sys.exit()

while not sensor.value():
    time.sleep(0.1)


speed = 0
distance = 0
TSS = 0


WIFI_SSID       = ssid
WIFI_PASSWORD   = passwd
ADAFRUIT_IO_URL = 'io.adafruit.com'
mqtt_client_id  = bytes('odo', 'utf-8')

#feeds
SPEED_FEED_ID   = "speed"

led.on()



displayBuffer = [0,[0,0],0,0]


####################
## PROGRAM STARTS ##
####################


def connect():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.disconnect()
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    if not wifi.isconnected():
        print('connecting..')
        timeout = 0
        while (not wifi.isconnected() and timeout < 10):
            print(10 - timeout)
            timeout = timeout + 1
            time.sleep(1) 
    if(wifi.isconnected()):
        print('connected')
    else:
        print('not connected')
        sys.exit()
        

def updateCloud(inputs):
    global speed
    #publish feeds
    client.publish(speed_feed,    
                  bytes(str(speed), 'utf-8'),   # Publishing Temprature to adafruit.io
                  qos=0)
    print("sent")
    speed += 1


def cb(topic, msg):                             # Callback function
    print('Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    

def updateLcd():
    pass

def secs():
    return time.ticks_ms() / 1000
    
    
def trunc(N, ndigits=0):
    return math.trunc(N * 10 ** ndigits) / 10 ** ndigits


###############
## STOPWATCH ##
###############
        
    
class stopwatch:
    def __init__(self):
        self.start_time = 0.0
        self.times = []
        self.run = False
    
    def start(self):
        if not self.run:
            self.start_time = secs()
            self.run = True
        
    def get_time(self):
        tbr = 0
        if self.run:
            tbr = secs() - self.start_time
        for times in self.times:
            tbr += times
        return tbr
    
    def get_secs(self):
        tbr = float(trunc(self.get_time() % 60, 1))
        if tbr >= 10:
            return str(tbr)
        else:
            return "0" + str(tbr)
    
    def get_mins(self):
        tbr = int(trunc(self.get_time() / 60) % 60)
        return f"{tbr:02d}"
    
    def get_hrs(self):
        return str(int(trunc(self.get_time() / 3600)))
    
    def reset(self):
        self.start_time = secs()
        self.run = True
        self.times = []
        
    def stop(self):
        if self.run:
            self.times.append(secs() - self.start_time)
            self.run = False
            
            
###################
## STOPWATCH END ##
###################



if __name__ == '__main__':
    connect()
    
    client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=userid, 
                    password=key,
                    ssl=False)
    
    try:            
        client.connect()
    except Exception as e:
        print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
        sys.exit()
        
    speed_feed = bytes('{:s}/feeds/{:s}'.format(userid, SPEED_FEED_ID), 'utf-8')
    
    throttle   = bytes('{:s}/throttle'.format(userid), 'utf-8')
    
    client.set_callback(cb)      # Callback function               
    client.subscribe(throttle) # Subscribing to particular topic
    
    publishSpeedTimer = Timer()
    publishSpeedTimer.init(period=2500, mode=Timer.PERIODIC, callback = updateCloud)
        
    
    while True:
        try:
            client.check_msg()                  # non blocking function
        except :
            client.disconnect()
            sys.exit()
