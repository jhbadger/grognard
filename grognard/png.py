"""Write a Surface (or raw rgb bytes) to a PNG file, for screenshots."""

import struct
import zlib


def write_png(path, w, h, rgb_bytes):
    raw = b''.join(b'\x00' + rgb_bytes[y * w * 3:(y + 1) * w * 3]
                   for y in range(h))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b'IDAT', zlib.compress(raw, 6)))
        f.write(chunk(b'IEND', b''))


def save_surface(surf, path, zoom=1):
    if zoom == 1:
        write_png(path, surf.w, surf.h, bytes(surf.buf))
        return
    w, h = surf.w, surf.h
    out = bytearray()
    for y in range(h):
        row = surf.buf[y * w * 3:(y + 1) * w * 3]
        zr = b''.join(bytes(row[x * 3:x * 3 + 3]) * zoom for x in range(w))
        out += zr * zoom
    write_png(path, w * zoom, h * zoom, bytes(out))
