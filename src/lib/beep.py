from machine import Pin, PWM
import time

class Beep(object):
    """
    Beep with PWM.
    """

    def __init__(self, pin_num = 23):
        self.pin_num = pin_num
        self.pwm = None

    def init(self):
        if self.pwm is None:
            self.pwm = PWM(Pin(self.pin_num, Pin.OUT))
        self.pwm.duty(0)

    def deinit(self):
        self.pwm.duty(0)
        self.pwm.deinit()
        self.pwm = None

    def play(self, notes):
        self.init()
        for f in notes:
            if f == 0:
                pass
            elif f == None:
                self.pwm.duty(0)
            else:
                self.pwm.freq(f)
                self.pwm.duty(512)
            time.sleep(0.4)

    def mac(self, length = 2):
        notes = [784, 698, 784, None] * 3
        for i in range(length):
            self.play(notes)
            time.sleep(0.5)
        self.deinit()

    def famima(self):
        notes = [None, 1760, 1396, 1048, 1396, 1568, 2092, 0, 1568, 1760, 1568, 1048, 1396, 0, None]
        # notes = [None, 880, 698, 524, 698, 784, 1046, 0, 784, 880, 784, 524, 698, 0, None]
        # notes = [None, 440, 349, 262, 349, 392, 523, 0, 392, 440, 392, 262, 349, 0, None]
        self.play(notes)
        self.deinit()
