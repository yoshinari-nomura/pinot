import time

# DATASHEET SEARCH SITE | WWW.ALLDATASHEET.COM
# http://image.dfrobot.com/image/data/SEN0097/BH1750FVI.pdf

class BH1750(object):
    """
    Interface to the ROHM BH1750 Digital 16bit Serial Output Type
    Ambient Light Sensor IC. addr would be 0x23 or 0x56.
    """
    def __init__(self, i2c, addr=0x23):
        """
        Initialize a sensor with I2C and ADDRESS.
        """
        if i2c == None:
            raise ValueError('I2C required')
        self._i2c = i2c
        self._addr = addr

    def lux(self):
        """
        Get light-intensity in high resolution mode.
        """
        # Power on (0x01)
        self._i2c.writeto(self._addr, "\x01")
        time.sleep_ms(100)

        # One Time H-Resolution Mode 0010_0000 (0x20)
        # max 240ms
        self._i2c.writeto(self._addr, "\x20")
        time.sleep_ms(240)

        val = self._i2c.readfrom(self._addr, 2)
        return ((val[0] << 8) + val[1]) / 1.2
