"""Packaging a game: its icon, a macOS app, and a folder for Buildozer to
make an Android app of (built in Docker, as the tilerpgs are).

    ./yourgame --build-app [folder]       writes <Title>.app
    ./yourgame --build-android folder     writes the Buildozer project
    ./yourgame --icon-png SIZE [out.png]  writes just the icon

A game names its icon with ICON: a function registered with
@grognard.icon('name') that draws it at any size.
"""

import glob
import os
import plistlib
import shutil
import struct
import sys
import zlib

from . import icon_image


def game_files(gdef):
    """The game's script and the modules beside it that are its own:
    ID_*.py and any in FILES."""
    script = os.path.realpath(gdef.__file__)
    here = os.path.dirname(script)
    extra = set(glob.glob(os.path.join(here, gdef.ID + '_*.py')))
    for name in getattr(gdef, 'FILES', []):
        extra.add(os.path.join(here, name))
    return script, sorted(extra)


def engine_dir():
    return os.path.dirname(os.path.abspath(__file__))


def copy_engine(dest):
    target = os.path.join(dest, 'grognard')
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(engine_dir(), target,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


# ------------------------------------------------------------------- icon

def icon_png(gdef, size):
    """RGBA PNG bytes of the game's icon at size x size."""
    n = min(size, 256)
    img = icon_image(gdef, n)
    px = img.pixels()
    rows = []
    for y in range(size):
        sy = min(img.h - 1, y * img.h // size)
        row = bytearray([0])
        for x in range(size):
            c = px[sy * img.w + min(img.w - 1, x * img.w // size)]
            row += bytes(c) + b'\xff' if c else b'\0\0\0\0'
        rows.append(bytes(row))

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) +
            chunk(b'IEND', b''))


# ICNS entry types holding PNG data, with the pixel size of each
ICNS_TYPES = [(b'icp4', 16), (b'icp5', 32), (b'ic11', 32), (b'ic12', 64),
              (b'ic07', 128), (b'ic13', 256), (b'ic08', 256),
              (b'ic14', 512), (b'ic09', 512)]


def icns(gdef):
    """An .icns file written directly (no iconutil needed)."""
    pngs = {}
    body = b''
    for tag, size in ICNS_TYPES:
        if size not in pngs:
            pngs[size] = icon_png(gdef, size)
        body += tag + struct.pack('>I', len(pngs[size]) + 8) + pngs[size]
    return b'icns' + struct.pack('>I', len(body) + 8) + body


# ------------------------------------------------------------------ macOS

def build_app(gdef, dest):
    """A macOS <Title>.app in dest, holding a copy of the game and the
    engine, started with the Python that built it."""
    name = gdef.TITLE.replace('/', '-')
    app = os.path.join(dest, name + '.app')
    if os.path.exists(app):
        shutil.rmtree(app)
    macos = os.path.join(app, 'Contents', 'MacOS')
    res = os.path.join(app, 'Contents', 'Resources')
    os.makedirs(macos)
    os.makedirs(res)
    script, extra = game_files(gdef)
    shutil.copy(script, os.path.join(res, gdef.ID + '.py'))
    for f in extra:
        shutil.copy(f, res)
    copy_engine(res)
    launcher = os.path.join(macos, gdef.ID)
    with open(launcher, 'w') as fh:
        fh.write('#!/bin/sh\nexec "%s" "$(dirname "$0")/../Resources/%s.py" '
                 '"$@"\n' % (sys.executable, gdef.ID))
    os.chmod(launcher, 0o755)
    with open(os.path.join(res, gdef.ID + '.icns'), 'wb') as fh:
        fh.write(icns(gdef))
    info = {
        'CFBundleName': name,
        'CFBundleDisplayName': name,
        'CFBundleIdentifier': 'org.grognard.' + gdef.ID,
        'CFBundleExecutable': gdef.ID,
        'CFBundleIconFile': gdef.ID,
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': '1.0',
        'NSHighResolutionCapable': True,
    }
    with open(os.path.join(app, 'Contents', 'Info.plist'), 'wb') as fh:
        plistlib.dump(info, fh)
    return app


# ---------------------------------------------------------------- Android

ANDROID_SPEC = """\
[app]
title = %(title)s
package.name = %(id)s
package.domain = org.grognard
source.dir = .
source.include_exts = py,png
# (files with no extension get in regardless: keep the build's tar out)
source.exclude_patterns = tar
version = 1.0
# Kivy draws it; pyjnius reaches Android's MediaPlayer for the sound.
# Kivy's recipe brings requests, and requests charset-normalizer, which
# python-for-android would fetch as a compiled Android wheel and then fail
# to install; naming its pure-Python wheel here keeps it out of the way.
requirements = python3,kivy,pyjnius,charset-normalizer@https://files.pythonhosted.org/packages/fc/ad/d07d7862a62ffa6d79d68074d14823243dd235a77c45262acbf6adeb28bf/charset_normalizer-3.5.2-py3-none-any.whl
orientation = landscape, portrait
fullscreen = 0
icon.filename = %%(source.dir)s/icon.png
presplash.filename = %%(source.dir)s/icon.png
android.presplash_color = #000000
# 64-bit ARM only: nearly every phone, and what the Play Store asks for.
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
"""


ANDROID_TAR = r'''#!/home/user/.venv/bin/python3
"""tar, for the kivy/buildozer image on a Mac.  Its GNU tar unpacks with
the openat2 system call, which neither Rosetta nor QEMU can run, so every
unpacking fails ("Cannot mkdir: Function not implemented").  This unpacks
with Python's tarfile instead, refusing paths that leave the folder as GNU
tar does, and hands anything else to the real tar.  Written by
--build-android, and mounted over the image's tar."""
import os
import sys
import tarfile

REAL = "/usr/bin/tar"


def real():
    os.execv(REAL, [REAL] + sys.argv[1:])


def main(args):
    if not args:
        real()
    first = args[0].lstrip("-")
    if args[0].startswith("--") or not first.isalpha() or "x" not in first:
        real()                      # not unpacking: the real tar can
    archive, dest, strip = None, ".", 0
    rest = args[1:]
    if "f" in first:
        if not rest:
            real()
        archive, rest = rest[0], rest[1:]
    while rest:
        a = rest.pop(0)
        if a == "-C" and rest:
            dest = rest.pop(0)
        elif a.startswith("--strip-components="):
            strip = int(a.split("=", 1)[1])
        elif a.startswith("--") and a in (
                "--no-same-owner", "--no-same-permissions", "--overwrite"):
            pass
        else:
            real()                  # members or options we don't know
    if archive is None or archive == "-":
        real()
    with tarfile.open(archive) as tf:
        members = []
        for m in tf.getmembers():
            if strip:
                parts = m.name.split("/")[strip:]
                if not parts or not parts[0]:
                    continue
                m.name = "/".join(parts)
            members.append(m)
        tf.extractall(dest, members=members, filter="tar")


main(sys.argv[1:])
'''


ANDROID_BUILD = r'''#!/bin/sh
# Build the Android app with Buildozer in Docker (kivy/buildozer), from
# this folder wherever it's run from: ./build.sh, or ./build.sh with
# Buildozer's own arguments (default: -v android debug).  The APK lands in
# bin/.  Written by --build-android, like the tilerpgs' build.sh.
#
#   buildozer-home      Docker volume: Android's SDK and NDK.
#   buildozer-platform  Docker volume: python-for-android and all it has
#                       compiled, shared by every project built this way.
#   tar                 this folder's tar, over the image's own, which can't
#                       unpack under Intel emulation on a Mac.
#   .android            this folder's, as the container's ~/.android: the
#                       debug key the APK is signed with.  Keep it, or the
#                       next build won't install over this one.
set -e
cd "$(dirname "$0")"
[ $# -gt 0 ] || set -- -v android debug
exec docker run --rm --platform linux/amd64 \
    -v buildozer-home:/home/user/.buildozer \
    -v "$PWD":/home/user/hostcwd \
    -v buildozer-platform:/home/user/hostcwd/.buildozer/android/platform \
    -v "$PWD/tar":/usr/local/bin/tar:ro \
    -v "$PWD/.android":/home/user/.android \
    -v "$PWD/.android":/root/.android \
    --entrypoint /bin/bash kivy/buildozer -c \
    'rm -rf /home/user/hostcwd/.buildozer/android/platform/build-*/build/venv
     exec /usr/local/bin/entrypoint.sh "$@"' build "$@"
'''


def build_android(gdef, dest):
    """A folder for Buildozer to make an Android app of: the game as
    main.py, the engine, its icon, a buildozer.spec (written only if there
    isn't one, so your changes to it stay), and build.sh and the tar it
    uses for building in Docker."""
    os.makedirs(dest, exist_ok=True)
    for name, text in (('tar', ANDROID_TAR), ('build.sh', ANDROID_BUILD)):
        path = os.path.join(dest, name)
        with open(path, 'w') as fh:
            fh.write(text)
        os.chmod(path, 0o755)
    script, extra = game_files(gdef)
    shutil.copy(script, os.path.join(dest, 'main.py'))
    for f in extra:
        shutil.copy(f, dest)
    copy_engine(dest)
    with open(os.path.join(dest, 'icon.png'), 'wb') as fh:
        fh.write(icon_png(gdef, 512))
    spec = os.path.join(dest, 'buildozer.spec')
    if not os.path.exists(spec):
        with open(spec, 'w') as fh:
            fh.write(ANDROID_SPEC % {'title': gdef.TITLE, 'id': gdef.ID})
    return dest
