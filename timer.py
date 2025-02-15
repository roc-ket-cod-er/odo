import math
import time

def secs():
    return time.ticks_ms() / 1000
    
    
def trunc(N, ndigits=0):
    return math.trunc(N * 10 ** ndigits) / 10 ** ndigits
        
    
class timer:
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