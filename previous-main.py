import time, machine, math, random
from machine import Pin, reset, ADC
from _thread import allocate_lock, start_new_thread
from customLCD import display
from timer import *
from time import sleep
import sys

lock = allocate_lock()
sensor = Pin(18, Pin.IN, Pin.PULL_UP)
run = Pin(19, Pin.IN, Pin.PULL_UP)

if run.value():
    sys.exit()

while not sensor.value():
    time.sleep(0.1)
    


displayBuffer = [0,[0,0],0,0]

class odometer:
    def __init__(self, WHEEL, lock):
        self.m = 0.0
        self.WHEEL = WHEEL
        self.timeB = 0.0
        self.timeA = secs()
        self.speed = 0
        self.avg = 0
        self.display = display(20, 4)
        self.timer = timer()
        self.lock = lock
        start_new_thread(core1, (self, self.lock,))
    
    
    def checkspeed(self):
        time = secs() - self.timeA
        return self.WHEEL / time
    
    
    def add(self):
        self.lock.acquire()
        self.timer.start()
        
        self.timeB = secs()
        time = self.timeB - self.timeA
        self.timeA = secs()
        
        self.m += self.WHEEL
        self.m = round(self.m, 2)
        self.speed = self.WHEEL / time
        if self.timer.get_time() > 0:
            self.avg = self.m / self.timer.get_time() * 3.6
        self.speed = round(self.speed * 3.6, 1)
        self.lock.release()
        
    def update_lcd(self):
        lock.acquire()
        
        if self.timer.get_time() > 0:
            self.avg = self.m / self.timer.get_time() * 3.6
            
        displayBuffer = [round(self.m),
                        [self.timer.get_mins(), self.timer.get_secs()],
                        self.speed,
                        round(self.avg, 1)]
        lock.release()
        return displayBuffer
    
    
    def reset(self):
        self.m = 0


def core1(self, lock):
    global displayBuffer
    
    adc = ADC(4)
    display = self.display
    
    while True:

        buffer = self.update_lcd()
        
        adc_v = adc.read_u16() * (3.3 / 65536)
        temp = 29 - (adc_v - 0.706) / 0.001721
        
        m = buffer[0]
        time = buffer[1]
        speed = buffer[2]
        avg = buffer[3]
        print(buffer, sensor.value(), temp)
        
        display.resetBuffer() #reset the lcd buffer
        display.putWithEnding(m, ending="m")  #display the meters
        display.putWithEnding(str(time[0]) + ":" + str(time[1]), ending="s")  #display the time
        display.putWithEnding(speed, ending="km/h")  #display the speed
        display.putWithEnding(avg, prefix="avg:")  #display the average speed
        display.putBuffer() #display the buffer
        sleep(2)

def core0():
    odo = odometer(1.6, lock)
    t = timer()
    while True:
        if not sensor.value():
            odo.add()
            t.reset()
            t.start()
            while not sensor.value():
                time.sleep_ms(30)
        time.sleep_ms(1)

if __name__ == '__main__':
    #pausetime = float(input("wait "))
    try:
        core0()
    finally:
        machine.reset()
        
