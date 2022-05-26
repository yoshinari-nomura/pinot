# Sample main.py

################################################################
# helpers

################
# Initializers for small display panels

def panel_ili9341(spi):
    from ili9341 import ILI934X
    panel = ILI934X(spi, cs = Pin(17), dc = Pin(5), rst = Pin(4))

    # check if write/read pixel is working
    panel.pixel(0, 0, 0xffff)
    if panel.pixel(0, 0) != 0:
        return panel
    return None

def panel_st7735(spi):
    from ST7735 import TFT
    panel = TFT(spi, 26, 25, 27) # DC=26, RST=25, CS=27
    panel.initb2()
    panel.rotation(0) # 1: 128x160 → 160x128
    panel.setvscroll(1,1)
    return panel

def setup_panel(name, i2c_or_spi):
    if i2c_or_spi is None:
        return None

    if isinstance(i2c_or_spi, SPI):
        spi = i2c_or_spi
        panel = panel_ili9341(spi) or panel_st7735(spi)

    if isinstance(i2c_or_spi, SoftI2C):
        i2c = i2c_or_spi
        if 0x3c in i2c.scan():
            from ssd1306 import SSD1306_I2C
            panel = SSD1306_I2C(128, 32, i2c, 0x3c)

    print("Display panel:", panel)
    return panel

################
# Interface to sensors

class PinotSensor:
    """
    Interface to some I2C sensor
    """
    def __init__(self, i2c = None, addr = None):
        """
        Initialize a sensor.
        """
        from scd30 import SCD30

        if i2c == None:
            raise ValueError('I2C required')
        if addr == None:
            raise ValueError('I2C address required')

        self.i2c = i2c
        self.addr = addr
        self.thing = SCD30(i2c, addr)

    def get_value(self):
        import time
        while self.thing.get_status_ready() != 1:
            print("Wait for CO2 sensor ready.")
            time.sleep_ms(200)
        return self.thing.read_measurement()

################
# MQTT sub callback

def mqtt_callback(topic, msg, retained, duplicate):
    import beep
    global disp
    print((topic, msg))

    if msg.startswith('W, '):
        disp.text(str(msg.replace('W, ', '', 1), 'utf-8'))
        beep.Beep().famima()
    else:
        disp.text(str(msg, 'utf-8'))

################################################################
# main loop thread

def main_thread(thing, pubsub, disp):
    import time

    print("main_thread start")
    trial, error, pubtime = 0, 0, 0

    while True:
        trial += 1

        try:
            value = thing.get_value()
            pubsub.publish('{{"co2": {:.0f}, "temperature": {:.1f}, "humidity": {:.0f}}}'.format(*value))
            pubtime = time.ticks_ms()
        except:
            value = None
            error += 1

        print("Value:", value)

        if value is not None:
            disp.echo("V:{:.0f},{:.1f},{:.0f}\n".format(*value))
            disp.echo("E/T {}/{}".format(error, trial), lineno = 1)

        while time.ticks_diff(time.ticks_ms(), pubtime) < 60000:
            pubsub.check_msg()
            time.sleep(1)

################################################################
# main

import _thread

from machine import SoftI2C, Pin, SPI
from display import PinotDisplay
from pnfont import Font
from pubsub import PubSub
from jsonconfig import JsonConfig
jsonconfig = JsonConfig()

i2c = SoftI2C(scl = Pin(19), sda = Pin(18))
spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))

disp = PinotDisplay(panel = setup_panel('ST7735', spi), font = Font('/fonts/shnmk14u.pfn'))
disp.clear()

thing = PinotSensor(i2c, 0x61)
pubsub = PubSub(jsonconfig, mqtt_callback)

_thread.start_new_thread(main_thread, (thing, pubsub, disp))
