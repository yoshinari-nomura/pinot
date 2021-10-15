class PinotDisplay:
    """
    Interface to small I2C display panel
    """
    def __init__(self, panel = None, font = None):
        """
        Initialize a display.
        """
        self.font = font
        self.panel = panel

    def echo(self, msg, lineno = 0):
        print(msg)
        if self.panel is not None:
            if lineno == 0:
                self.panel.fill(0)
            self.panel.text(msg, 0, lineno * 10, 1)
            self.panel.show()

    def banner(self, msg, lineno = 0):
        for char in msg:
            print(char)
            try:
                glyph = self.font.glyph(char)
                print(glyph.banner())
            except:
                pass

    def text(self, msg, lineno = 0):
        if lineno == 0:
            self.panel.fill(0)

        sx, spc = 0, self.font.glyph(' ')
        sy = lineno * spc.height

        for char in msg:
            if char == '\n':
                sx = 0
                sy += spc.height
                continue

            glyph = self.font.glyph(char)
            if glyph is None:
                continue
            self.__put_glyph(sx, sy, glyph)
            sx += glyph.width
        self.panel.show()

    def __put_glyph(self, sx, sy, glyph):
        for y in range(0, glyph.height):
            for x in range(0, glyph.width):
                pix = glyph.pixel(x, y)
                self.panel.pixel(sx + x, sy + y, pix)

################################################################
## main

if __name__ == '__main__':
    from machine import Pin, SoftI2C
    from ssd1306 import SSD1306_I2C
    from pnfont import Font
    import sys

    if len(sys.argv) > 1:
        sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])


    i2c  = SoftI2C(scl = Pin(22), sda = Pin(21))
    disp = PinotDisplay(panel = SSD1306_I2C(128, 32, i2c, addr = 0x3c),
                        font  = Font('/fonts/shnmk14u.pfn'))

    disp.text('本日は晴天\n気温 25℃')
    disp.banner('桃太郎')
