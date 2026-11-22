"""The Tk front end: a window showing the game's framebuffer, scaled to
fit, and the keyboard and mouse passed through to the game (a click is a
tap; dragging scrolls the map; the wheel scrolls it too).  The game's
text is drawn over the picture as canvas text in a real font, so it stays
smooth however far the picture is scaled up."""

import time
import tkinter as tk
from tkinter import font as tkfont

from . import textfont
from .widgets import screen_size

W, H = 640, 480

KEYS = {
    'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right',
    'Return': 'enter', 'KP_Enter': 'enter', 'Escape': 'esc',
    'BackSpace': 'backspace', 'Delete': 'backspace', 'Tab': 'tab',
    'space': 'space', 'F1': 'f1', 'question': '?',
    'KP_Up': 'up', 'KP_Down': 'down', 'KP_Left': 'left', 'KP_Right': 'right',
}
IGNORE = {'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
          'Meta_L', 'Meta_R', 'Super_L', 'Super_R', 'Caps_Lock'}

# zoom / subsample pairs Tk can scale an image by, smallest first
SCALES = [(1, 1), (3, 2), (2, 1), (5, 2), (3, 1), (7, 2), (4, 1), (5, 1)]


class TkShell:
    def __init__(self, game, scale=None):
        self.g = game
        self.root = tk.Tk()
        self.root.title(game.title)
        self.root.configure(bg='black')
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        z = 1
        for (a, b) in SCALES:
            if W * a / b <= sw * 0.92 and H * a / b <= sh * 0.85:
                z = (a, b)
        if scale:
            z = (int(scale * 2), 2)
        self.zoom = z
        ww, wh = W * z[0] // z[1], H * z[0] // z[1]
        self.root.geometry('%dx%d' % (ww, wh))
        self.root.minsize(360, 480)
        self.canvas = tk.Canvas(self.root, width=ww, height=wh, bg='black',
                                highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        self.img = None
        self.ox = self.oy = 0
        self.win = (ww, wh)             # the window's size
        self.fsize = (W, H)             # the size of the picture shown
        self.root.bind('<Key>', self.on_key)
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<MouseWheel>', self.on_wheel)
        self.canvas.bind('<Button-4>', lambda e: self.wheel(0, -1))
        self.canvas.bind('<Button-5>', lambda e: self.wheel(0, 1))
        self.root.bind('<Configure>', self.on_resize)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.full = False
        self.last = time.time()
        self.set_icon()
        self.fit()
        # smooth text
        fs = textfont.spec(game.d)
        self.family = fs['family'] or \
            tkfont.nametofont('TkDefaultFont').actual()['family']
        self.fsize_factor = fs['size']
        self.bold = fs['bold']
        self.fonts = {}
        self.pool = []              # canvas text items, reused each frame
        game.measure = self.measure

    def set_icon(self):
        try:
            from . import icon_image
            img = icon_image(self.g.d, 48)
            px = img.pixels()
            ph = tk.PhotoImage(width=img.w, height=img.h)
            rows = []
            for y in range(img.h):
                rows.append('{' + ' '.join(
                    '#%02x%02x%02x' % (px[y * img.w + x] or (0, 0, 0))
                    for x in range(img.w)) + '}')
            ph.put(' '.join(rows))
            self.root.iconphoto(True, ph)
            self._icon = ph
        except tk.TclError:
            pass

    @property
    def z(self):
        return self.zoom[0] / self.zoom[1]

    def font(self, scale):
        """(Font, how far above the text's top its line starts)."""
        n = textfont.pixels(scale, self.z, self.fsize_factor)
        bold = self.bold or scale >= 2
        f = self.fonts.get((n, bold))
        if f is None:
            font = tkfont.Font(family=self.family, size=-n,
                               weight='bold' if bold else 'normal')
            lift = font.metrics('ascent') - n * textfont.CAPS
            f = self.fonts[(n, bold)] = (font, lift)
        return f

    def measure(self, s, scale):
        """The width of s in the game's pixels."""
        return self.font(scale)[0].measure(s) / self.z

    def draw_texts(self, texts):
        z = self.z
        jobs = []
        for (x, y, t, col, shadow, scale) in texts or ():
            font, lift = self.font(scale)
            X = self.ox + x * z
            Y = self.oy + y * z - lift
            if shadow:
                d = max(1, round(z * (0.6 if scale < 1 else 1)))
                jobs.append((X + d, Y + d, t, shadow, font))
            jobs.append((X, Y, t, col, font))
        c = self.canvas
        for i, (X, Y, t, col, font) in enumerate(jobs):
            fill = '#%02x%02x%02x' % col
            if i < len(self.pool):
                item = self.pool[i]
                c.coords(item, X, Y)
                c.itemconfig(item, text=t, fill=fill, font=font,
                             state='normal')
            else:
                self.pool.append(c.create_text(X, Y, text=t, fill=fill,
                                               font=font, anchor='nw'))
        for item in self.pool[len(jobs):]:
            c.itemconfig(item, state='hidden')

    def toggle_fullscreen(self, e=None):
        self.full = not self.full
        self.root.attributes('-fullscreen', self.full)

    def on_resize(self, e):
        if e.widget is not self.root:
            return
        if (e.width, e.height) == self.win:
            return
        self.win = (e.width, e.height)
        self.fit()
        self.g.dirty = True

    def fit(self):
        """Choose the scale for the window's size, and tell the game how
        big a screen fills it (an upright window, a phone held upright,
        gets the upright layout)."""
        ww, wh = self.win
        sc, size, portrait = screen_size(ww, wh,
                                         [a / b for a, b in SCALES])
        self.zoom = [z for z in SCALES if z[0] / z[1] == sc][0]
        self.g.set_screen(size, portrait)
        self.place()

    def place(self):
        """Centre the picture in the window (there's at most a sliver of
        border, where the window doesn't divide exactly)."""
        fw, fh = self.fsize
        ww, wh = self.win
        a, b = self.zoom
        self.ox = max(0, (ww - fw * a // b) // 2)
        self.oy = max(0, (wh - fh * a // b) // 2)
        self.canvas.coords(self.item, self.ox, self.oy)

    def on_key(self, e):
        ks = e.keysym
        if ks in IGNORE:
            return
        k = KEYS.get(ks)
        if k is None:
            if e.char and e.char.isprintable():
                k = e.char
            else:
                k = ks.lower()
        if k and len(k) == 1 and k.isalpha():
            k = k.lower()
        self.g.key(k)
        self.after_input()

    def to_game(self, e):
        a, b = self.zoom
        return (e.x - self.ox) * b // a, (e.y - self.oy) * b // a

    def on_press(self, e):
        x, y = self.to_game(e)
        if 0 <= x < self.fsize[0] and 0 <= y < self.fsize[1]:
            self.g.press(x, y)
            self.pressed = True
        else:
            self.pressed = False

    def on_drag(self, e):
        if getattr(self, 'pressed', False):
            x, y = self.to_game(e)
            self.g.drag(x, y)
            if self.g.dirty:
                self.draw()

    def on_release(self, e):
        if getattr(self, 'pressed', False):
            self.pressed = False
            x, y = self.to_game(e)
            self.g.release(x, y)
            self.after_input()

    def on_wheel(self, e):
        self.wheel(0, -1 if e.delta > 0 else 1)

    def wheel(self, dx, dy):
        self.g.wheel(dx, dy)
        if self.g.dirty:
            self.draw()

    def after_input(self):
        if self.g.quit:
            self.on_close()
            return
        self.draw()

    def on_close(self):
        try:
            if not self.g.quit and not self.g.e.over:
                self.g.save()
        finally:
            self.g.sound.stop()
            self.root.destroy()

    def draw(self):
        s = self.g.frame()
        if (s.w, s.h) != self.fsize:
            self.fsize = (s.w, s.h)
            self.place()
            s = self.g.frame()      # again, the text measured at the new size
        img = tk.PhotoImage(data=s.ppm(), format='PPM')
        a, b = self.zoom
        if a != 1:
            img = img.zoom(a)
        if b != 1:
            img = img.subsample(b)
        self.img = img
        self.canvas.itemconfig(self.item, image=img)
        self.draw_texts(s.texts)

    def tick(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        self.g.update(dt)
        if self.g.quit:
            self.on_close()
            return
        if self.g.dirty:
            self.draw()
        self.root.after(33, self.tick)

    def run(self):
        self.draw()
        self.root.after(33, self.tick)
        self.root.mainloop()
