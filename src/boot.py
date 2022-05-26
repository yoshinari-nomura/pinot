# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()

import sys
sys.path.reverse()

################
# Wait boot button pressed until timeout.

def wait_on_boot(timeout_ms = 5000):
    """Wait boot button pressed until timeout.
    if boot is pressed, returns 'config' else 'app'
    """
    import time
    from machine import Pin

    boot = Pin(0, Pin.IN, Pin.PULL_UP)
    while timeout_ms > 0:
        if timeout_ms % 1000 == 0:
            print("boot.py: BOOT {}".format(timeout_ms // 1000))
        if boot.value() == 0:
            return 'config'
        time.sleep_ms(200)
        timeout_ms -= 200

    return 'app'

################
# Copy specific application file to main.py

def copy_file_to_main(name):
    """Copy /apps/NAME.py file to /main.py, if NAME.py exists.
    """
    try:
        src = '/apps/' + name + '.py'
        dst = '/main.py'

        print('Copy {} to {}'.format(src, dst))

        src = open(src, 'rb')
        content = src.read()
        src.close()

        dst = open(dst, 'wb')
        dst.write(content)
        dst.close()
    except:
        pass

################
# main

import gc
from jsonconfig import JsonConfig
from connection import WiFi

global pinot_conf
global pinot_wifi
global pinot_mode

pinot_conf = JsonConfig()
pinot_wifi = WiFi()
pinot_mode = wait_on_boot()

print("boot.py: booting as {} mode".format(pinot_mode))

################
# start Wi-Fi as STATION with fallback to AP mode

pinot_wifi.start(pinot_conf)

if not pinot_wifi.isconnected():
    print("No Wi-Fi connection, fallback to config mode")
    pinot_mode = 'config'
else:
    print("Wi-Fi connected")

################
# Invoke application or fallback to config.py

app_name = pinot_conf.get('app_name')

if app_name is None or pinot_mode == 'config':
    app_name = 'config'

print('Invoking application:', app_name)
copy_file_to_main(app_name)

gc.collect()
