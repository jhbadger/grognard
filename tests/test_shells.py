"""The front ends: the Tk window (skipped where there's no Tk or no
display) and the Kivy one (skipped where Kivy isn't installed).  Each
opens a real window for a few seconds, so set GROGNARD_NO_GUI=1 to skip
them."""

import os
import subprocess
import sys
import unittest

import util

NAME = os.environ.get('GROGNARD_GAME') or util.games()[0]
NO_GUI = bool(os.environ.get('GROGNARD_NO_GUI'))

# Driving a window needs its main loop, so each check runs as a little
# script of its own.
TK = r'''
import sys
sys.path.insert(0, %(tests)r)
import util
from grognard.tkshell import TkShell
g = util.new_game(util.load(%(game)r))
sh = TkShell(g)
errors = []
sh.root.report_callback_exception = lambda *a: errors.append(a)
out = []
def wide():
    sh.draw()
    out.append(sh.fsize)
    # press and release on the scroll pad's middle, through the canvas
    wd, r = [(w, r) for w, r in g.layout.items if w.name == 'phase'][0]
    a, b = sh.zoom
    x, y = r[0] + r[2] // 2, r[1] + r[3] // 2
    for ev in ('<ButtonPress-1>', '<ButtonRelease-1>'):
        sh.canvas.event_generate(ev, x=sh.ox + x * a // b,
                                 y=sh.oy + y * a // b)
    sh.root.after(300, upright)
def upright():
    out.append(g.e.phase)
    sh.root.geometry('420x780')
    sh.root.after(600, done)
def done():
    sh.draw()
    out.append(sh.fsize)
    sh.root.destroy()
sh.root.after(600, wide)
sh.run()
# the screens: wide at first; upright, and filling the window, after
w, h = out[0]
w2, h2 = out[2]
a, b = sh.zoom
out[0] = 'wide' if w >= 640 and h >= 480 and w > h else out[0]
out[2] = 'upright' if h2 > w2 and abs(420 - w2 * a // b) < a and \
    abs(780 - h2 * a // b) < a else out[2]
print(out, len(errors))
'''

KIVY = r'''
import sys
sys.path.insert(0, %(tests)r)
import util
from grognard.kivyshell import KivyShell
g = util.new_game(util.load(%(game)r))
sh = KivyShell(g, 450, 850)
out = []
class T:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.ud = {}
def go(dt):
    sh.draw()
    out.append(sh.fsize)
    sh.key_down(None, 101, 0, 'e', [])
    out.append(g.e.phase)
    t = T(sh.ox + 100 * sh.scale, sh.oy + (sh.fsize[1] - 100) * sh.scale)
    sh.root.on_touch_down(t)
    sh.root.on_touch_up(t)
    sh.Clock.schedule_once(lambda dt: sh.close(), 0.2)
sh.Clock.schedule_once(go, 1.0)
sh.run()
# upright, and filling the window (450 x 850, in its own pixels)
w, h = out[0]
ww, wh = sh.Window.size
out[0] = 'upright' if h > w and abs(ww - w * sh.scale) < sh.scale + 1 \
    and abs(wh - h * sh.scale) < sh.scale + 1 else out[0]
print(out)
'''


def run(script, python=sys.executable):
    p = subprocess.run([python, '-c', script % {
        'tests': os.path.dirname(os.path.abspath(__file__)), 'game': NAME}],
        capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout.strip().splitlines()[-1:] or [''], p.stderr


def has(module, python=sys.executable):
    return subprocess.run([python, '-c', 'import ' + module],
                          capture_output=True).returncode == 0


class Shells(unittest.TestCase):
    @unittest.skipIf(NO_GUI or not has('tkinter'), 'no Tk, or GUI tests off')
    def test_tk(self):
        code, last, err = run(TK)
        self.assertEqual(code, 0, err)
        self.assertEqual(last[0], "['wide', 'combat', 'upright'] 0", err)

    @unittest.skipIf(NO_GUI or not has('kivy',
                                       os.environ.get('KIVY_PYTHON',
                                                      sys.executable)),
                     'no Kivy (set KIVY_PYTHON to a Python that has it)')
    def test_kivy(self):
        code, last, err = run(KIVY, os.environ.get('KIVY_PYTHON',
                                                  sys.executable))
        self.assertEqual(code, 0, err)
        self.assertEqual(last[0], "['upright', 'combat']", err[-2000:])


if __name__ == '__main__':
    unittest.main()
