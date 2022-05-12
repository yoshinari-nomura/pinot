# panel should have:
#   Panel.width
#   Panel.height
#   Panel.glyph(glyph, sx, sy)
#    or Panel.pixel(x, y, color)
#   Panel.fill_rect(x1, y1, w, h, color)
#
# Optional:
#   Panel.fill(color)
#   Panel.show()
#   Panel.scroll(dy)
#
# FBConsole() のための要件
#  fill(self, color)                  画面をcolorで塗りつぶす (画面消去用)
#  fill_rect(self, x, y, w, h, color) 塗りつぶした矩形を描く  (行消去用)
#  scroll(self, dx, dy)               dy ピクセル縦スクロールする (横スクロールは不要)
#  hline(self, x, y, w, color)        水平線を描く (カーソル表示用)
#  text(self, char, x, y, color)      1文字描く

class PinotDisplay:
    """
    Interface to small I2C display panel
    """
    def __init__(self, panel = None, font = None):
        """
        Initialize a display.
        """
        self.panel = panel

        self.font = font
        self.line_height = font.glyph(' ').height + 1

        self.cx = 0
        self.cy = 0
        self.top = 0

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

    def clear(self):
        self.panel.fill(0)
        self.cx = 0
        self.cy = 0

    def scroll(self, dy):
        self.panel.scroll(dy, 0)
        self.top = (self.top + dy) % self.panel.height

    def absolute_y(self, cy):
        return (self.panel.height - self.top + cy) % self.panel.height

    def line_feed(self):
        self.cx = 0
        bottom = (self.cy + self.line_height * 2 - 1) % self.panel.height

        # if wrapped
        if self.absolute_y(bottom) < self.absolute_y(self.cy):
            self.scroll(self.absolute_y(bottom) + 1)

        self.cy = (self.cy + self.line_height) % self.panel.height
        self.panel.fill_rect(0, self.cy,
                                  self.panel.width, self.line_height,
                                  0)

    def locate(self, x, y):
        self.cx = x
        self.cy = y

    def text(self, msg):
        for char in msg:
            if char == '\n':
                self.line_feed()
                continue

            glyph = self.font.glyph(char)

            if glyph is None:
                continue

            if self.cx + glyph.width >= self.panel.width:
                self.line_feed()

            self.__put_glyph(self.cx, self.cy, glyph)
            self.cx += glyph.width
        if callable(getattr(self.panel, "show", None)):
            self.panel.show()

    def __put_glyph(self, sx, sy, glyph):
        if callable(getattr(self.panel, "glyph", None)):
            self.panel.glyph(glyph, sx, sy)
        else:
            for y in range(0, glyph.height):
                for x in range(0, glyph.width):
                    pix = glyph.pixel(x, y)
                    self.panel.pixel(sx + x, sy + y, pix * 65535)

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
