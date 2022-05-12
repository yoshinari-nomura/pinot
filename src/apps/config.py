# Simple config.py

################################################################
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
# Setup display

from machine import Pin, SoftI2C, SPI

try:
    i2c = SoftI2C(scl = Pin(22), sda = Pin(21))
    spi = SPI(1, baudrate = 40000000, miso = Pin(12), sck = Pin(14), mosi = Pin(13))
    disp = Display(i2c = i2c, spi = spi)
except:
    disp = Display()

################################################################
# main

import _thread

def config_thread(disp):
    disp.echo("config_thread start")

    from jsonconfig import JsonConfig
    from configserver import ConfigServer

    httpd = ConfigServer(JsonConfig())
    disp.echo("Open {}".format(pinot_wifi.ifconfig()[0]))
    httpd.serv()

_thread.start_new_thread(config_thread, (disp, ))
