# Sample main.py

################
# Interface to small I2C SSD1306 OLED display

class PinotDisplay:
    """
    Interface to small I2C display
    """
    def __init__(self, i2c = None, addr = None):
        """
        Initialize a display.
        """

        self.disp = None

        if i2c is not None:
            from ssd1306 import SSD1306_I2C
            if addr is not None:
                self.disp = SSD1306_I2C(128, 32, i2c, addr)
            else:
                self.disp = SSD1306_I2C(128, 32, i2c)

    def echo(self, msg, lineno=0):
        print(msg)
        if self.disp is not None:
            if lineno == 0:
                self.disp.fill(0)
            self.disp.text(msg, 0, lineno * 10, 1)
            self.disp.show()

################
# Interface to some I2C sensor

class PinotSensor:
    """
    Interface to some I2C sensor
    """
    def __init__(self, i2c = None, addr = None):
        """
        Initialize a sensor.
        """
        from bh1750 import BH1750

        if i2c == None:
            raise ValueError('I2C required')
        self.i2c  = i2c
        self.addr = addr

        if addr is not None:
            self.thing = BH1750(i2c, addr)
        else:
            self.thing = BH1750(i2c)

    def get_value(self):
        return self.thing.lux()

################
# main thread

def main_thread():
    print("main_thread start")
    from thingspeak import ThingSpeak
    from jsonconfig import JsonConfig
    import time
    import mqtt

    global disp
    global i2c

    config = JsonConfig()
    ths_apikey = (config.get('thingspeak_apikey') or '')
    mqtt_topic = (config.get('mqtt_pub_topic') or '')

    thing = PinotSensor(i2c, 0x23)

    if mqtt_topic != '':
        mqtt_client = mqtt.mqtt_create_client(config)
        mqtt_client.connect()

    if ths_apikey != '':
        ths_client = ThingSpeak(ths_apikey)

    sent, error = 0, 0
    while True:
        value = thing.get_value()
        try:
            if mqtt_topic != '':
                mqtt_client.publish(mqtt_topic, str(value))

            if ths_apikey != '':
                code = thingspeak.post(field1 = value)
                if code != 200:
                    error += 1
        except:
            error += 1
        sent += 1
        disp.echo("V:{:.1f}".format(value))
        disp.echo("E/S {}/{}".format(error, sent), lineno=1)
        time.sleep(60)

################
# config thread

def config_thread():
    print("config_thread start")

    global disp
    from jsonconfig import JsonConfig
    from configserver import ConfigServer

    httpd = ConfigServer(JsonConfig())
    disp.echo("Open 192.168.4.1", lineno=1)
    httpd.serv()

################
# Boot settings

import time
import _thread
from connection import WiFi
from jsonconfig import JsonConfig
from machine import Pin, SoftI2C

conf = JsonConfig()
boot = Pin(0, Pin.IN, Pin.PULL_UP)

try:
    i2c  = SoftI2C(scl=Pin(22), sda=Pin(21))
    disp = PinotDisplay(i2c = i2c, addr = 0x3c)
except:
    disp = PinotDisplay()

mode = 'station'
wifi = WiFi()

wait_on_boot = 5 * 1000 # ms

# Check boot button for 5seconds. if pressed, falls into AP mode.
while wait_on_boot > 0:
    if wait_on_boot % 1000 == 0:
        disp.echo("BOOT BTN to AP {}".format(wait_on_boot // 1000))
    if boot.value() == 0:
        mode = "ap"
        break
    time.sleep_ms(200)
    wait_on_boot -= 200

disp.echo("Mode: {}".format(mode))

if mode == 'station':
    # start station with fallback to AP mode
    wifi.start(conf)
    if not wifi.isconnected():
        disp.echo("Wi-Fi failed")
        mode = 'ap'
else:
    wifi.start_ap()

try:
    if mode == 'station':
        pass
        _thread.start_new_thread(main_thread, ())
    else:
        _thread.start_new_thread(config_thread, ())
except:
    disp.echo("Fatal Error {}".format(mode), lineno=2)
