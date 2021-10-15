from struct import unpack

# 1st byte mask:
# | 1st byte            | prefix mask      | value mask       |
# |---------------------+------------------+------------------|
# | 0xxxxxxx (0x00 + x) | 1000_0000 (0x80) | 0111_1111 (0x7f) |
# | 110xxxxx (0xc0 + x) | 1110_0000 (0xe0) | 0001_1111 (0x1f) |
# | 1110xxxx (0xe0 + x) | 1111_0000 (0xf0) | 0000_1111 (0x0f) |
# | 11110xxx (0xf0 + x) | 1111_1000 (0xf8) | 0000_0111 (0x07) |
#
def utf8_to_codepoint(char):
    if len(char) == 0:
        return None

    b1, *b234 = bytes(char, 'UTF-8')

    if b1 & 0x80 == 0x00:
        return utf8_to_code234(b1 & 0x7f, b234)
    if b1 & 0xe0 == 0xc0:
        return utf8_to_code234(b1 & 0x1f, b234)
    if b1 & 0xf0 == 0xe0:
        return utf8_to_code234(b1 & 0x0f, b234)
    if b1 & 0xf8 == 0xf0:
        return utf8_to_code234(b1 & 0x07, b234)
    return None

# 2nd, 4rd, 4th byte mask:
# | nth byte            | prefix mask      | value mask       |
# |---------------------+------------------+------------------|
# | 10xxxxxx (0x80 + x) | 1100_0000 (0xc0) | 0011_1111 (0x3f) |
#
def utf8_to_code234(b1, b234):
    code = b1
    for bx in b234:
        if bx & 0xc0 != 0x80:
            return None
        code = (code << 6) | (bx & 0x3f)
    return code

def codepoint_to_size(codepoint):
    if codepoint <= 0xff:
        return 1
    elif codepoint <= 0xffff:
        return 2
    else:
        return 4

class Font:
    def __init__(self, font_filename):
        self.font_filename = font_filename

    def glyph(self, char):
        """Find font Glyph by UTF-8 char
        """

        codepoint = utf8_to_codepoint(char)

        if codepoint is None:
            return None

        with open(self.font_filename, 'rb') as fp:
            fp.seek(16) # Skip header
            pos = 16

            while True:
                block_header = fp.read(6)

                if len(block_header) != 6:
                    return None

                width, height, codepoint_size, attribute, num_chars = \
                    unpack('<BBBBH', block_header)
                pos += 6
                entry_size = (width * height + 7) // 8 + codepoint_size

                head = pos
                tail = head + entry_size * (num_chars - 1)

                label = '<' + '?BH?I'[codepoint_size]

                head_codepoint, = unpack(label, fp.read(codepoint_size))
                fp.seek(tail)
                tail_codepoint, = unpack(label ,fp.read(codepoint_size))

                fp.seek(tail + entry_size)
                pos = tail + entry_size

                if codepoint < head_codepoint:
                    return None
                elif tail_codepoint < codepoint:
                    continue
                else:
                    break

            bitmap = self.bsearch_bitmap(fp, codepoint, head, tail, entry_size)
            if bitmap is not None:
                return Glyph(char, width, height, bitmap)
            else:
                return None

    def bsearch_bitmap(self, font_fp, target, head_pos, tail_pos, entry_size):
        """B-search font glyph bitmap in region
        target is UTF-32 codepoint
        """

        head = 0
        tail = (tail_pos - head_pos) // entry_size

        codepoint_size = codepoint_to_size(target)
        label = '<' + '?BH?I'[codepoint_size]

        font_fp.seek(head_pos)

        while head <= tail:
            mid = (head + tail) // 2

            font_fp.seek(head_pos + entry_size * mid)
            code, = unpack(label, font_fp.read(codepoint_size))

            if code < target:
                head = mid + 1
            elif code > target:
                tail = mid - 1
            else:
                return font_fp.read(entry_size - codepoint_size)

class Glyph:
    def __init__(self, char, width, height, bitmap):
        self.char, self.width, self.height, self.bitmap = char, width, height, bitmap

    def pixel(self, x, y):
        i = x + y * self.width
        if self.bitmap[i // 8] & (0x01 << ( 7 - i % 8)) != 0:
            return 1
        else:
            return 0

    def banner(self):
        if self.bitmap is None:
            return ''
        banner = ''
        for y in range(0, self.height):
            for x in range(0, self.width):
                pix = self.pixel(x, y)
                if pix == 1:
                    banner += '#'
                else:
                    banner += '.'
            banner += '\n'
        return banner
