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
import ina226_jcf


lock = allocate_lock()

lcd = display(20, 4)

i2c = I2C(1, sda=Pin(2), scl=Pin(3))
if i2c.scan() == []:
    lcd.put("INA226 NOT DETECTED")
    print("INA226 NOT DETECTED")
    sys.exit()
else:
    print("INA226 DETECTED")
    lcd.put("LCD detected!")
    
ina226 = ina226_jcf.INA226(i2c, Rs=0.1)

time.sleep_ms(100)


sensor = Pin(18, Pin.IN, Pin.PULL_UP)
run = Pin(19, Pin.IN, Pin.PULL_UP)
led = Pin("LED", Pin.OUT)

if not run.value():
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
SPEED_FEED_ID     = "speed"
AVG_SPEED_FEED_ID = "avg-speed"
BATTERY_FEED_ID   = "battery-percent"

led.on()



####################
## PROGRAM STARTS ##
####################


def connect():
    connecting = "connecting"
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
            time.sleep(0.5)
            connecting += '.'
            if connecting == 'connecting....':
                connecting = 'connecting'
            lcd.put(connecting)
            
            time.sleep(0.5)
            connecting += '.'
            if connecting == 'connecting....':
                connecting = 'connecting'
            lcd.put(connecting)
            
    if(wifi.isconnected()):
        print('connected')
    else:
        print('not connected')
        sys.exit()
        
battTally = 6
def updateCloud(inputs):
    global speed, battTally
    
    if battTally % 2 == 0:
        
        V, I, P = ina226.get_VIP()
        print(V, I, P)
        
        speed = (odo.getKmph())
        #publish feeds
        client.publish(speed_feed,    
                      bytes(str(speed), 'utf-8'),   # Publishing speed to adafruit.io
                      qos=0)
        
        client.publish(avg_speed_feed,    
                      bytes(str(odo.getAvgKmph()), 'utf-8'),   # Publishing AVERAGE SPEED to adafruit.io
                      qos=0)
        if battTally == 6:
            client.publish(battery_feed,
                          bytes(str(V/0.15), 'utf-8'),   # Publishing Battery Percentage to adafruit.io
                          qos=0)
            battTally = 0
        print(battTally, V/0.15)
        print("sent")
    updateLcd()
    battTally += 1


def cb(topic, msg):                             # Callback function
    print('Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    

def updateLcd():
    lcd.resetBuffer() #reset the lcd buffer
    lcd.putWithEnding(odo.getDistance(), ending="m")  #display the meters
    lcd.putWithEnding(str(odo.time.get_mins()) + ":" + str(odo.time.get_secs()), ending="s")  #display the time
    lcd.putWithEnding(round(speed, 2), ending="km/h")  #display the speed
    lcd.putWithEnding(odo.getAvgKmph(), prefix="avg:")  #display the average speed
    lcd.putBuffer() #display the buffer

def secs():
    return time.ticks_ms() / 1000
    
    
def trunc(N, ndigits=0):
    return math.trunc(N * 10 ** ndigits) / 10 ** ndigits

def avg(inp):
    try:
        return sum(inp) / len(inp)
    except ZeroDivisionError:
        return 0


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

##############
## ODOMETER ##
##############
            
class odometer:
    def __init__(self, wheel):
        self.stopwatch = stopwatch()
        self.stopwatch.start()
        self.speed = 0
        self.speeds = [0]
        self.WHEEL = wheel
        self.distance = 0
        self.time = stopwatch()
        self.time.start()
    
    def hit(self):
        self.speed = self.WHEEL / self.stopwatch.get_time()
        self.stopwatch.reset()
        self.speeds.append(round(self.speed,2))
        self.distance += self.WHEEL
        
    def getSpeed(self):
        return(self.speed)
    
    def getAvgSpeed(self):
        ret = avg(self.speeds)
        print(self.speeds, ret)
        self.speeds = []
        return ret
    
    def getKmph(self):
        return(self.getAvgSpeed() * 3.6)
    
    def getDistance(self):
        return self.distance
    
    def getAvg(self):
        return self.distance / self.time.get_time()
    
    def getAvgKmph(self):
        return self.getAvg() * 3.6
        
            
##################
## ODOMETER END ##
##################


if __name__ == '__main__':
    lcd.put("connecting")
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
    avg_speed_feed = bytes('{:s}/feeds/{:s}'.format(userid, AVG_SPEED_FEED_ID), 'utf-8')
    battery_feed = bytes('{:s}/feeds/{:s}'.format(userid, BATTERY_FEED_ID), 'utf-8')
    
    throttle   = bytes('{:s}/throttle'.format(userid), 'utf-8')
    
    client.set_callback(cb)      # Callback function               
    client.subscribe(throttle) # Subscribing to particular topic
    
    odo = odometer(2.5)
    
    publishSpeedTimer = Timer()
    updateCloud("")
    publishSpeedTimer.init(period=2500, mode=Timer.PERIODIC, callback = updateCloud)
        
    hit = 0
    
    while True:
        try:
            client.check_msg()                  # non blocking function
        except :
            client.disconnect()
            sys.exit()
            
        if not sensor.value():
            hit += 1
            print("hit", hit)
            odo.hit()
            time.sleep_ms(100)
            while not sensor.value():
                time.sleep_ms(1)
                
        time.sleep_ms(1)
            
            