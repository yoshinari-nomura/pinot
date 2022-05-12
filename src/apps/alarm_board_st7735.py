# Sample main.py

################################################################
# helpers

################
# Interface to small displays SD1306 or ILI9341.

class Display:
    """Interface to a display SD1306 or ILI9341.
    SSD1306 should be: 128x32, I2C ADDR=0x3c, SDA=21, SCL=22
    ILI9341 should be: 240x320, SPI1 MISO=12, MOSI=13, SCK=14, CS=17, DC=5, RST=4
    """

    def __init__(self, i2c = None, spi = None):
        """
        Initialize a display SD1306 or ILI9341.
        """

        from display import PinotDisplay
        from pnfont import Font

        self.panel = self.__setup_panel(i2c, spi)
        if self.panel is not None:
            self.font  = Font('/fonts/shnmk16u.pfn')
            self.disp  = PinotDisplay(self.panel, self.font)
            self.disp.clear()

    def __setup_panel(self, i2c, spi):
        """Setup display SD1306 or ILI9341.
        SSD1306 should be: 128x32, I2C ADDR=0x3c, SDA=21, SCL=22
        ILI9341 should be: 240x320, SPI1 MISO=12, MOSI=13, SCK=14, CS=17, DC=5, RST=4
        """
        from machine import Pin, SoftI2C, SPI

        panel = None

        if i2c is not None and 0x3c in i2c.scan():
            from ssd1306 import SSD1306_I2C
            panel = SSD1306_I2C(128, 32, i2c, 0x3c)

        if spi is not None:
            from ili9341 import ILI934X
            dev = ILI934X(spi, cs = Pin(17), dc = Pin(5), rst = Pin(4))
            # check if write/read pixel is working
            dev.pixel(0, 0, 0xffff)
            if dev.pixel(0, 0) != 0:
                panel = dev

        print("Display panel:", panel)
        return panel

    def echo(self, msg, lineno=0):
        print(msg)
        if self.panel is not None:
            if lineno == 0:
                self.disp.clear()
            else:
                self.disp.text('\n')
            self.disp.text(msg)

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
# Interface to publish

class PubSub:
    """Interface to publish/subscribe
    """

    def __init__(self, callback_function):
        from thingspeak import ThingSpeak
        from jsonconfig import JsonConfig
        import mqtt

        self.thingspeak = None
        self.mqtt = None

        config = JsonConfig()
        apikey = (config.get('thingspeak_apikey') or '')
        self.mqtt_pub_topic = (config.get('mqtt_pub_topic') or '')
        self.mqtt_sub_topic = (config.get('mqtt_sub_topic') or '')

        if self.mqtt_pub_topic != '' or self.mqtt_sub_topic != '':
            print("Setup MQTT connection")
            self.mqtt = mqtt.mqtt_create_client(config)
            self.mqtt.connect()

        if self.mqtt_pub_topic != '':
            print("Setup MQTT pub topic:", self.mqtt_pub_topic)

        if self.mqtt_sub_topic != '':
            print("Setup MQTT sub topic:", self.mqtt_sub_topic)
            self.mqtt.set_callback(callback_function)
            self.mqtt.subscribe(self.mqtt_sub_topic)

        if apikey != '':
            print("Setup ThingSpeak")
            self.thingspeak = ThingSpeak(apikey)

    def check_msg(self):
        return self.mqtt.check_msg()

    def is_conn_issue(self):
        return self.mqtt.is_conn_issue()

    def reconnect(self):
        return self.mqtt.reconnect()

    def resubscribe(self):
        return self.mqtt.resubscribe()

    def publish(self, value):
        error_count = 0

        if self.mqtt:
            try:
                print("Publish to MQTT")
                self.mqtt.publish(self.mqtt_pub_topic, str(value))
            except:
                print("MQTT publish error")
                error_count += 1

        if self.thingspeak:
            print("Publish to ThingSpeak")
            if self.thingspeak.post(field1 = value) != 200:
                print("ThingSpeak publish error")
                error_count += 1

        if error_count > 0:
            print("Publish error")
            raise "Publish error"

################################################################
# main loop thread

def sound():
    from machine import Pin, PWM
    import time

    tick = 0.25
    notes_freq = [784, 698, 784, 0] * 3
    pwm = PWM(Pin(23, Pin.OUT))
    pwm.duty(0)

    for f in notes_freq:
        if f:
            pwm.freq(f)
            pwm.duty(512)
        else:
            pwm.duty(0)
        time.sleep(tick)

    pwm.duty(0)
    pwm.deinit()

def mqtt_callback(topic, msg, retained, duplicate):
    import beep
    global disp
    print((topic, msg))
    disp.clear()
    disp.text(str(msg, 'utf-8'))
    beep.Beep().famima()


def main_thread(thing, pubsub, disp):
    import time

    print("main_thread start")
    trial, error = 0, 0

    while True:
        trial += 1
        value = None

        c = 0
        while c < 60:
            if pubsub.is_conn_issue():
                while pubsub.is_conn_issue():
                    pubsub.reconnect()
                    c += 1
                    time.sleep(1)
                else:
                    pubsub.resubscribe()
            pubsub.check_msg()
            c += 1
            time.sleep(1)

        try:
            value = thing.get_value()
            pubsub.publish(value)
        except:
            error += 1

        print("Value:", value)

        if value is not None:
            disp.echo("V:{:.1f}".format(value))
            disp.echo("E/T {}/{}".format(error, trial), lineno = 1)

################################################################
# main

from machine import SoftI2C, Pin, SPI
import _thread
from ST7735 import TFT
from display import PinotDisplay
from pnfont import Font

try:
    i2c = SoftI2C(scl = Pin(22), sda = Pin(21))
    spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
    display = TFT(spi, 5, 4, 27) # DC=5, RST=4, CS=27
    display.initb2()
    display.rotation(0) # 1: 128x160 → 160x128
    display.rgb(True)
    disp = PinotDisplay(panel = display, font  = Font('/fonts/shnmk14u.pfn'))
except:
    disp = Display()

thing = PinotSensor(i2c)
pubsub = PubSub(mqtt_callback)

_thread.start_new_thread(main_thread, (thing, pubsub, disp))
