# This file is derived from: https://github.com/tab4moji/M5StackCoreLCD

import time
import ustruct
import framebuf

_COLUMN_SET = const(0x2a)
_PAGE_SET = const(0x2b)
_RAM_WRITE = const(0x2c)
_RAM_READ = const(0x2e)
_DISPLAY_ON = const(0x29)
_WAKE = const(0x11)
_LINE_SET = const(0x37)
_MADCTL = const(0x36)
_DISPLAY_INVERSION_ON = const(0x21)

def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

class ILI934X:
    """
    A simple driver for the ILI9341/ILI9340-based displays.

    >>> import ili9341
    >>> from machine import Pin, SPI
    >>> spi = SPI(1, baudrate=40000000, miso=Pin(12), sck=Pin(14), mosi=Pin(13))
    >>> display = ili9341.ILI934X(spi, cs=Pin(17), dc=Pin(5), rst=Pin(4))
    >>> display.fill(ili9341.color565(0xff, 0x11, 0x22))
    >>> display.pixel(120, 160, 0)
    """

    width, height = 240, 320

    def __init__(self, spi, cs, dc, rst):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.reset()
        self.init()
        self._scroll = 0

    def init(self):
        for command, data in (
            (0xef, b'\x03\x80\x02'),
            (0xcf, b'\x00\xc1\x30'),
            (0xed, b'\x64\x03\x12\x81'),
            (0xe8, b'\x85\x00\x78'),
            (0xcb, b'\x39\x2c\x00\x34\x02'),
            (0xf7, b'\x20'),
            (0xea, b'\x00\x00'),
            (0xc0, b'\x23'),  # Power Control 1, VRH[5:0]
            (0xc1, b'\x10'),  # Power Control 2, SAP[2:0], BT[3:0]
            (0xc5, b'\x3e\x28'),  # VCM Control 1
            (0xc7, b'\x86'),  # VCM Control 2
            (0x36, b'\x48'),  # Memory Access Control
            (0x3a, b'\x55'),  # Pixel Format
            (0xb1, b'\x00\x18'),  # FRMCTR1
            (0xb6, b'\x08\x82\x27'),  # Display Function Control
            (0xf2, b'\x00'),  # 3Gamma Function Disable
            (0x26, b'\x01'),  # Gamma Curve Selected
            (0xe0,  # Set Gamma
             b'\x0f\x31\x2b\x0c\x0e\x08\x4e\xf1\x37\x07\x10\x03\x0e\x09\x00'),
            (0xe1,  # Set Gamma
             b'\x00\x0e\x14\x03\x11\x07\x31\xc1\x48\x08\x0f\x0c\x31\x36\x0f'),
        ):
            self._write(command, data)

        self._write(_WAKE)
        time.sleep_ms(120)
        self._write(_DISPLAY_ON)

    def reset(self):
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

    def _write(self, command, data=None):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        self.cs.value(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        if data is not None and len(data) > 0:
            self.dc.value(1)
            self.cs.value(0)
            self.spi.write(data)
            self.cs.value(1)

    def _block(self, x0, y0, x1, y1, data=None):
        self._write(_COLUMN_SET, ustruct.pack(">HH", x0, x1))
        self._write(_PAGE_SET, ustruct.pack(">HH", y0, y1))
        if data is None:
            return self._read(_RAM_READ, (x1 - x0 + 1) * (y1 - y0 + 1) * 3)
        self._write(_RAM_WRITE, data)

    def _read(self, command, count):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        dummy = self.spi.read(1)
        data = self.spi.read(count)
        self.cs.value(1)
        return data

    def pixel(self, x, y, color=None):
        if color is None:
            r, g, b = self._block(x, y, x, y)
            return color565(r, g, b)
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return
        self._block(x, y, x, y, ustruct.pack(">H", color))

    def fill_rect(self, x, y, w, h, color):
        x = min(self.width - 1, max(0, x))
        y = min(self.height - 1, max(0, y))
        w = min(self.width - x, max(1, w))
        h = min(self.height - y, max(1, h))
        self._block(x, y, x + w - 1, y + h - 1, b'')
        chunks, rest = divmod(w * h, 512)
        if chunks:
            data = ustruct.pack(">H", color) * 512
            for count in range(chunks):
                self._data(data)
        data = ustruct.pack(">H", color) * rest
        self._data(data)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def char(self, char, x, y, color=0xffff, background=0x0000):
        buffer = bytearray(8)
        framebuffer = framebuf.FrameBuffer1(buffer, 8, 8)
        framebuffer.text(char, 0, 0)
        color = ustruct.pack(">H", color)
        background = ustruct.pack(">H", background)
        data = bytearray(2 * 8 * 8)
        for c, byte in enumerate(buffer):
            for r in range(8):
                if byte & (1 << r):
                    data[r * 8 * 2 + c * 2] = color[0]
                    data[r * 8 * 2 + c * 2 + 1] = color[1]
                else:
                    data[r * 8 * 2 + c * 2] = background[0]
                    data[r * 8 * 2 + c * 2 + 1] = background[1]
        self._block(x, y, x + 7, y + 7, data)

    def glyph(self, glyph, x, y, color=0xffff, background=0x0000):
        fg1, fg2 = ustruct.pack(">H", color)
        bg1, bg2  = ustruct.pack(">H", background)
        data = bytearray()
        for b in glyph.bitmap:
            p0 = (b >> 7) & 1
            p1 = (b >> 6) & 1
            p2 = (b >> 5) & 1
            p3 = (b >> 4) & 1
            p4 = (b >> 3) & 1
            p5 = (b >> 2) & 1
            p6 = (b >> 1) & 1
            p7 = (b >> 0) & 1
            data.extend(bytearray([
                fg1 * p0 + bg1 * (1 - p0),
                fg2 * p0 + bg2 * (1 - p0),
                fg1 * p1 + bg1 * (1 - p1),
                fg2 * p1 + bg2 * (1 - p1),
                fg1 * p2 + bg1 * (1 - p2),
                fg2 * p2 + bg2 * (1 - p2),
                fg1 * p3 + bg1 * (1 - p3),
                fg2 * p3 + bg2 * (1 - p3),
                fg1 * p4 + bg1 * (1 - p4),
                fg2 * p4 + bg2 * (1 - p4),
                fg1 * p5 + bg1 * (1 - p5),
                fg2 * p5 + bg2 * (1 - p5),
                fg1 * p6 + bg1 * (1 - p6),
                fg2 * p6 + bg2 * (1 - p6),
                fg1 * p7 + bg1 * (1 - p7),
                fg2 * p7 + bg2 * (1 - p7)
            ]))
        self._block(x, y, x + glyph.width -1, y + glyph.height - 1, data)

    def text(self, text, x, y, color=0xffff, background=0x0000, wrap=None,
             vwrap=None, clear_eol=False):
        if wrap is None:
            wrap = self.width - 8
        if vwrap is None:
            vwrap = self.height - 8
        tx = x
        ty = y

        def new_line():
            nonlocal tx, ty

            tx = x
            ty += 8
            if ty >= vwrap:
                ty = y

        for char in text:
            if char == '\n':
                if clear_eol and tx < wrap:
                    self.fill_rect(tx, ty, wrap - tx + 7, 8, background)
                new_line()
            else:
                if tx >= wrap:
                    new_line()
                self.char(char, tx, ty, color, background)
                tx += 8
        if clear_eol and tx < wrap:
            self.fill_rect(tx, ty, wrap - tx + 7, 8, background)

    def scroll(self, dy=None, dx=0):
        if dy is None:
            return self._scroll
        self._scroll = (self._scroll + dy) % self.height
        self._write(_LINE_SET, ustruct.pack('>H', self._scroll))

    def show(self):
        pass
