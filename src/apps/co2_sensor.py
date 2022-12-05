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
                self.disp.locate(0, lineno * 16)
                # self.disp.text('\n')
            self.disp.text(msg)

################
# Interface to sensors

class PinotSensorSCD30:
    """
    Interface to some I2C SCD30 sensor
    """
    def __init__(self, i2c = None, addr = None):
        """
        Initialize a sensor.
        """
        from scd30 import SCD30
        from jsonconfig import JsonConfig

        config = JsonConfig()
        self.asc_settings = (config.get('asc_settings') or '')

        if i2c == None:
            raise ValueError('I2C required')
        self.i2c  = i2c
        self.addr = addr

        if addr is not None:
            self.thing = SCD30(i2c, addr)
        else:
            self.thing = SCD30(i2c, 0x61)

        print('Setup ASC:',(self.asc_settings=='ON'))
        SCD30.set_automatic_recalibration(self.thing,(self.asc_settings=='ON'))

    def get_value(self):
        import time
        while self.thing.get_status_ready() != 1:
            print("Wait for CO2 sensor ready.")
            time.sleep_ms(200)
        return self.thing.read_measurement()

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
            try:
                self.mqtt.connect()
            except:
                print("MQTT connect failed")

        if self.mqtt_pub_topic != '':
            print("Setup MQTT pub topic:", self.mqtt_pub_topic)

        if self.mqtt_sub_topic != '' and callback_function is not None:
            print("Setup MQTT sub topic:", self.mqtt_sub_topic)
            self.mqtt.set_callback(callback_function)
            self.mqtt.subscribe(self.mqtt_sub_topic)
            # print("MQTT subscribe failed")

        if apikey != '':
            print("Setup ThingSpeak")
            self.thingspeak = ThingSpeak(apikey)

    def check_msg(self):
        if self.mqtt_pub_topic == '':
            return False
        self.mqtt.check_msg()

    def is_conn_issue(self):
        if self.mqtt_pub_topic == '':
            return False
        return self.mqtt.is_conn_issue()

    def reconnect(self):
        return self.mqtt.reconnect()

    def resubscribe(self):
        return self.mqtt.resubscribe()

    def publish(self, value):
        error_count = 0

        if self.mqtt:
            try:
                print("MQTT publish topic =", self.mqtt_pub_topic)
                self.mqtt.publish(self.mqtt_pub_topic, '{{"co2": {:.0f}, "temperature": {:.1f}, "humidity": {:.0f}}}'.format(value[0], value[1], value[2]))
            except:
                print("MQTT publish error")
                error_count += 1

        if self.thingspeak:
            print("Publish to ThingSpeak")
            if self.thingspeak.post(field1 = value[0],field2 = value[1],field3 =value[2]) != 200:
                print("ThingSpeak publish error")
                error_count += 1

        if error_count > 0:
            print("Publish error")
            raise "Publish error"

################################################################
# main loop thread

def mqtt_callback(topic, msg, retained, duplicate):
    import beep
    global disp
    print((topic, msg))
    # disp.clear()
    if msg.startswith('W, '):
        disp.echo(str(msg.replace('W, ', '', 1), 'utf-8'))
        beep.Beep().famima()
    else:
        disp.echo(str(msg, 'utf-8'))

def main_thread(thing, pubsub, disp):
    import time

    print("main_thread start")
    trial, error = 0, 0

    while True:
        trial += 1
        print("trial:", trial)
        value = None
        try:
            value = thing.get_value()
            print("Value:", value)
            pubsub.publish(value)
        except Exception as e:
            print("Error: value =", value, "error:", str(e))
            error += 1

        if value is not None:
            disp.echo("V:{:.0f},{:.1f},{:.0f}".format(value[0], value[1], value[2]))
            disp.echo("E/T {}/{}".format(error, trial), lineno = 1)

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


################################################################
# main

from machine import Pin, SoftI2C, SPI
import _thread
from machine import Pin, PWM
import time
from beep import Beep

try:
    i2c = SoftI2C(scl = Pin(22), sda = Pin(21))
    spi = SPI(1, baudrate = 40000000, miso = Pin(12), sck = Pin(14), mosi = Pin(13))
    disp = Display(i2c = i2c, spi = spi)
except:
    disp = Display()

# disp.clear()

thing = PinotSensorSCD30(i2c)
pubsub = PubSub(mqtt_callback)

_thread.start_new_thread(main_thread, (thing, pubsub, disp))
