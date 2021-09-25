from jsonconfig import JsonConfig
from connection import WiFi
from machine import Pin, SoftI2C
import time
import ssd1306
import _thread
from thingspeak import ThingSpeak

################
# Settings for SSD1306 OLED Display

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
disp = ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)
# disp = None

def echo(msg, lineno=0):
    global disp
    print(msg)
    if disp is not None:
        if lineno == 0:
            disp.fill(0)
        disp.text(msg, 0, lineno * 10, 1)
        disp.show()

################
# main thread

def main_thread():
    import onewire, ds18x20
    config = JsonConfig()
    ds = ds18x20.DS18X20(onewire.OneWire(Pin(32)))
    roms = ds.scan()
    thingspeak = ThingSpeak(config.get('thingspeak_apikey') or '')

    sent, error = 0, 0
    while True:
        # send convert command to all DS18B20
        ds.convert_temp()

        # Wait at least 750ms
        time.sleep_ms(750)

        measures = []
        for rom in roms:
            measures.append(ds.read_temp(rom))

        try:
            code = thingspeak.post_fields(measures)
            if code != 200:
                error += 1
        except:
            error += 1
        sent += 1
        echo("Temp:{:.1f}".format(measures[0]))
        echo("E/S {}/{}".format(error, sent), lineno=1)
        time.sleep(60)

################
# config thread

def config_thread():
    from configserver import ConfigServer
    httpd = ConfigServer(JsonConfig())
    httpd.serv()

################
# Boot settings

boot = Pin(0, Pin.IN, Pin.PULL_UP)
mode = 'station'
wifi = WiFi()
conf = JsonConfig(name = 'settings')
wait_on_boot = 5 * 1000 # ms

# Check boot button for 5seconds. if pressed, falls into AP mode.
while wait_on_boot > 0:
    if wait_on_boot % 1000 == 0:
        echo("BOOT BTN to AP {}".format(wait_on_boot // 1000))
    if boot.value() == 0:
        mode = "ap"
        break
    time.sleep_ms(200)
    wait_on_boot -= 200

echo("Mode: {}".format(mode))

if mode == 'station':
    # start station with fallback to AP mode
    wifi.start(conf)
    if not wifi.isconnected():
        echo("Wi-Fi conn failed")
        mode = 'ap'
else:
    wifi.start_ap()

try:
    if mode == 'station':
        pass
        _thread.start_new_thread(main_thread, ())
    else:
        _thread.start_new_thread(config_thread, ())
        echo("Open 192.168.4.1", lineno=1)
except:
    echo("Fatal Error {}".format(mode), lineno=2)
