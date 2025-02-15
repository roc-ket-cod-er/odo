from machine import I2C, Pin
from pico_i2c_lcd import I2cLcd
from time import sleep

class display:
    def __init__(self, x, y):
        self.prestr = ""
        self.buffer = ''
        self.x = x
        self.y = y
        self.cx = 0
        self.cy = 0
        
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        I2C_ADDR = i2c.scan()[0]
        #print(I2C_ADDR)
        self.lcd = I2cLcd(i2c, I2C_ADDR, y, x)
    
    
    def putwithoutnewline(self, string, x, y, delay=0):
        string += ' ' * (self.x * self.y - len(string) - 1)
        tstr=[[], string]
        self.cx = x
        self.cy = y
        i = 0
        for char in string:
            if len(self.prestr) == i:
                self.prestr += " "
                
            if char == self.prestr[i] and char != '\n':
                self.cx += 1
                tstr[0].append("-")
            else:
                self.lcd.move_to(self.cx, self.cy)
                self.lcd.putchar(char)
                sleep(delay)
                tstr[0].append(char)
                self.cx += 1
                
            i += 1
        
            if self.cx >= self.x:
                self.cx = 0
                self.cy += 1
                if self.cy >= self.y:
                    self.cy = 0
                    tstr[0].append("RESTART")
                else:    
                    tstr[0].append(self.cy + 100)
                
        #print(tstr, '\nin = \t\t', string, '\npre = \t\t', self.prestr)
        self.prestr = string
        
        
    def put(self, string, x=0, y=0, resetBuffer=True):
        tbr = ''
        i = 0
        for char in string:
            if char != '\n':
                tbr += char
                i += 1
            else:
                tbr += ' ' * ((self.x * self.y - i) % self.x)
                i = 0
                
        self.putwithoutnewline(tbr, x, y)
        
        if resetBuffer:
            self.buffer = '' 
    
    
    def putWithEnding(self, text, ending='', prefix='', w=10):
        placeholder = str(prefix)
        placeholder += str(text)
        placeholder += str(ending)
        placeholder += (w - len(placeholder)) * ' '
        self.buffer += placeholder[0:w]
        
        
    def resetBuffer(self):
        self.buffer = ''
        
        
    def putBuffer(self):
        self.put(self.buffer)
        

if __name__ == '__main__':
    dis = display(20, 4)
    dis.put('hi\nhi\nhi\nhi')

    while True:
        dis.put(input('>>'))
