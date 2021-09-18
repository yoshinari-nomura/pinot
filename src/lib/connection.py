import network
from binascii import hexlify
from time import sleep, ticks_ms, ticks_diff

class WiFi:
    """
    Interface to startup Wi-Fi
    """

    def __init__(self):
        self._ap = None
        self._sta = None

    @property
    def ap(self):
        return self._ap

    @property
    def sta(self):
        return self._sta

    def start_station(self, ssid, password, timeout = 10):
        self._sta = network.WLAN(network.STA_IF)
        if self._sta.isconnected():
            print('network config:', self._sta.ifconfig())
            return True

        print('Connecting to network', ssid, '...')
        self._sta.active(True)
        self._sta.connect(ssid, password)

        count = 0
        while count < timeout:
            sleep(1)
            count += 1
            print("Waiting Wi-Fi", count)
            if self._sta.isconnected():
                print('Connected:', self._sta.ifconfig())
                return True
        print('Failed.')
        self.stop_station()
        return False

    def stop_station(self):
        if self._sta != None:
            try:
                self._sta.disconnect()
                self._sta.active(False)
            except:
                pass
            self._sta = None

    def isconnected(self):
        return self._sta != None and self._sta.isconnected()

    def start_ap(self, ssid_prefix = 'pinot', password = 'pinot123'):
        self._ap = network.WLAN(network.AP_IF)
        ssid = ssid_prefix + '-' + str(hexlify(self._ap.config('mac'))[6:], 'ascii')
        self._ap.active(True)
        self._ap.config(essid = ssid, password = password, authmode = network.AUTH_WPA_WPA2_PSK)
        print('AP is open: SSID %s config: %s' % (ssid, self._ap.ifconfig()))

    def stop_ap(self):
        if self._ap != None:
            try:
                self._ap.disconnect()
                self._ap.active(False)
            except:
                pass
            self._ap = None

    def start(self, json_config):
        try:
            ssid = json_config.dict['wifi_ssid']
            password = json_config.dict['wifi_password']
            if not self.start_station(ssid, password):
                self.stop_station()
                pass
        except:
            pass
        if not self.isconnected():
            print('Fallback to AP mode')
            self.start_ap()
