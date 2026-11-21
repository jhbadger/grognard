"""Pixels (from blobber): colours, pictures with transparency, and the
framebuffer the whole screen is drawn into.  Pure Python; the front end
only has to show Surface.ppm()."""

from . import font as _font

BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def bayer(x, y):
    """Ordered-dither threshold in (0, 1) for pixel x, y."""
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0


def rgb(c):
    """A colour as an (r, g, b) tuple, from '#rrggbb' or a tuple."""
    if isinstance(c, tuple):
        return c
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t + 0.5)))
                 for i in range(3))


def scale(c, f):
    c = rgb(c)
    return tuple(max(0, min(255, int(v * f + 0.5))) for v in c)


def ramp(*stops, n=None):
    """A list of colours through the given stops (n entries if given)."""
    stops = [rgb(s) for s in stops]
    if n is None or n == len(stops):
        return stops
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(stops) - 1)
        j = min(int(t), len(stops) - 2)
        out.append(mix(stops[j], stops[j + 1], t - j))
    return out


class Image:
    """A picture with transparency, kept as rows of opaque runs
    (x, rgb bytes) so drawing it is a few slice copies per row."""
    __slots__ = ('w', 'h', 'rows')

    def __init__(self, w, h, rows):
        self.w, self.h, self.rows = w, h, rows

    @classmethod
    def from_pixels(cls, w, h, px):
        """px: row-major list of (r, g, b) or None for transparent."""
        rows = []
        for y in range(h):
            base = y * w
            runs = []
            x = 0
            while x < w:
                if px[base + x] is None:
                    x += 1
                    continue
                x0 = x
                parts = []
                while x < w and px[base + x] is not None:
                    parts.append(bytes(px[base + x]))
                    x += 1
                runs.append((x0, b''.join(parts)))
            rows.append(runs)
        return cls(w, h, rows)

    def pixels(self):
        px = [None] * (self.w * self.h)
        for y, runs in enumerate(self.rows):
            for x0, b in runs:
                for i in range(len(b) // 3):
                    px[y * self.w + x0 + i] = (b[3 * i], b[3 * i + 1],
                                               b[3 * i + 2])
        return px

    def scaled(self, nw, nh):
        """Nearest-neighbour resize."""
        nw, nh = max(1, int(nw)), max(1, int(nh))
        src = self.pixels()
        w, h = self.w, self.h
        xs = [min(w - 1, int((x + 0.5) * w / nw)) for x in range(nw)]
        out = []
        for y in range(nh):
            sy = min(h - 1, int((y + 0.5) * h / nh)) * w
            out.extend(src[sy + sx] for sx in xs)
        return Image.from_pixels(nw, nh, out)

    def flipped(self):
        px = self.pixels()
        w = self.w
        out = []
        for y in range(self.h):
            row = px[y * w:(y + 1) * w]
            out.extend(reversed(row))
        return Image.from_pixels(w, self.h, out)

    def shaded(self, f, fog=(0, 0, 0), dither=True):
        """Every pixel moved towards fog, keeping fraction f of itself; with
        dither the fraction is spread over two levels for a retro look."""
        if f >= 0.999:
            return self
        fog = rgb(fog)
        px = self.pixels()
        w = self.w
        steps = 8
        out = []
        for i, c in enumerate(px):
            if c is None:
                out.append(None)
                continue
            if dither:
                t = f * steps
                k = int(t)
                if t - k > bayer(i % w, i // w):
                    k += 1
                ff = min(1.0, k / steps)
            else:
                ff = f
            out.append(mix(fog, c, ff))
        return Image.from_pixels(w, self.h, out)


_TEXT_CACHE = {}


class Surface:
    """An RGB framebuffer."""

    def __init__(self, w, h, color=(0, 0, 0)):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(rgb(color)) * (w * h))
        self.clip = (0, 0, w, h)
        self._text_cache = _TEXT_CACHE      # shared: surfaces come and go

    # Clipping.

    def set_clip(self, x=0, y=0, w=None, h=None):
        if w is None:
            self.clip = (0, 0, self.w, self.h)
        else:
            self.clip = (max(0, x), max(0, y), min(self.w, x + w),
                         min(self.h, y + h))

    # Plain drawing.

    def fill(self, color):
        self.buf[:] = bytes(rgb(color)) * (self.w * self.h)

    def rect(self, x, y, w, h, color):
        cx0, cy0, cx1, cy1 = self.clip
        x0, y0 = max(x, cx0), max(y, cy0)
        x1, y1 = min(x + w, cx1), min(y + h, cy1)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(rgb(color)) * (x1 - x0)
        W3 = self.w * 3
        n = len(row)
        for yy in range(y0, y1):
            o = yy * W3 + x0 * 3
            self.buf[o:o + n] = row

    def frame(self, x, y, w, h, color, t=1):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def bevel(self, x, y, w, h, light, dark, t=1):
        """A raised edge: light top and left, dark bottom and right."""
        self.rect(x, y, w, t, light)
        self.rect(x, y, t, h, light)
        self.rect(x, y + h - t, w, t, dark)
        self.rect(x + w - t, y, t, h, dark)

    def pixel(self, x, y, color):
        cx0, cy0, cx1, cy1 = self.clip
        if cx0 <= x < cx1 and cy0 <= y < cy1:
            o = (y * self.w + x) * 3
            self.buf[o:o + 3] = bytes(rgb(color))

    def line(self, x0, y0, x1, y1, color):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        c = rgb(color)
        while True:
            self.pixel(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def translate(self, x, y, w, h, table):
        """Pass a rectangle's bytes through a 256-entry table (darken,
        tint one channel and so on)."""
        cx0, cy0, cx1, cy1 = self.clip
        x0, y0 = max(x, cx0), max(y, cy0)
        x1, y1 = min(x + w, cx1), min(y + h, cy1)
        if x0 >= x1 or y0 >= y1:
            return
        W3 = self.w * 3
        for yy in range(y0, y1):
            o = yy * W3 + x0 * 3
            e = o + (x1 - x0) * 3
            self.buf[o:e] = self.buf[o:e].translate(table)

    def darken(self, x, y, w, h, f):
        self.translate(x, y, w, h, bytes(int(i * f) for i in range(256)))

    # Blocks of bytes.

    def get(self, x, y, w, h):
        W3 = self.w * 3
        return b''.join(bytes(self.buf[(yy * self.w + x) * 3:
                                       (yy * self.w + x + w) * 3])
                        for yy in range(y, y + h))

    def put(self, x, y, w, h, data):
        """Copy an opaque w x h block of rgb bytes (no clipping beyond the
        surface itself)."""
        W3 = self.w * 3
        n = w * 3
        for j in range(h):
            yy = y + j
            if 0 <= yy < self.h:
                o = yy * W3 + x * 3
                self.buf[o:o + n] = data[j * n:(j + 1) * n]

    def blit(self, img, x, y):
        cx0, cy0, cx1, cy1 = self.clip
        x, y = int(x), int(y)
        W3 = self.w * 3
        buf = self.buf
        for j, runs in enumerate(img.rows):
            yy = y + j
            if yy < cy0 or yy >= cy1:
                continue
            base = yy * W3
            for rx, b in runs:
                sx = x + rx
                n = len(b) // 3
                a, e = 0, n
                if sx < cx0:
                    a = cx0 - sx
                if sx + n > cx1:
                    e = cx1 - sx
                if a >= e:
                    continue
                o = base + (sx + a) * 3
                buf[o:o + (e - a) * 3] = b[a * 3:e * 3]

    def blit_rows(self, ox, oy, rows):
        """Draw (y, x, bytes) rows already clipped to their area."""
        W3 = self.w * 3
        buf = self.buf
        for y, x, b in rows:
            o = (oy + y) * W3 + (ox + x) * 3
            buf[o:o + len(b)] = b

    # Text.

    def text_image(self, s, color, shadow=None, scale=1):
        key = (s, color, shadow, scale)
        img = self._text_cache.get(key)
        if img is not None:
            return img
        if len(self._text_cache) > 3000:
            self._text_cache.clear()
        w = max(1, _font.width(s, scale)) + (1 if shadow else 0)
        h = _font.HEIGHT * scale + (1 if shadow else 0)
        px = [None] * (w * h)
        layers = []
        if shadow:
            layers.append((1, rgb(shadow)))
        layers.append((0, rgb(color)))
        for off, col in layers:
            x = 0
            for ch in s:
                gw, runs = _font.glyph(ch)
                for gx, gy, n in runs:
                    for yy in range(gy * scale, (gy + 1) * scale):
                        row = (yy + off) * w
                        for xx in range((x + gx) * scale,
                                        (x + gx + n) * scale):
                            px[row + xx + off] = col
                x += gw + 1
        img = Image.from_pixels(w, h, px)
        self._text_cache[key] = img
        return img

    def text(self, x, y, s, color, shadow=None, scale=1, align='left'):
        """Draw s with its top-left (or top-centre, top-right) at x, y and
        return its width."""
        if not s:
            return 0
        color = rgb(color)
        shadow = rgb(shadow) if shadow else None
        img = self.text_image(s, color, shadow, scale)
        if align == 'center':
            x -= img.w // 2
        elif align == 'right':
            x -= img.w
        self.blit(img, x, y)
        return img.w

    def ppm(self):
        return b'P6 %d %d 255 ' % (self.w, self.h) + bytes(self.buf)
