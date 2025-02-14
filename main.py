from machine import Pin, Timer, ADC
import network
import time
from umqtt.robust import MQTTClient
import sys
import dht
import _thread
from secrets import passwd, ssid, userid, key

speed = 0

led = Pin("LED", Pin.OUT)

WIFI_SSID       = ssid
WIFI_PASSWORD   = passwd
ADAFRUIT_IO_URL = 'io.adafruit.com'
mqtt_client_id  = bytes('odo', 'utf-8')

#feeds
SPEED_FEED_ID   = "speed"

led.on()


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
        

def update(inputs):
    #publish feeds
    client.publish(speed_feed,    
                  bytes(str(speed), 'utf-8'),   # Publishing Temprature to adafruit.io
                  qos=0)
    print("sent")


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
    
    publishSpeedTimer = Timer()
    publishSpeedTimer.init(period=5000, mode=Timer.PERIODIC, callback = update)
        
    
    while True:
        try:
            client.check_msg()                  # non blocking function
        except :
            client.disconnect()
            sys.exit()
