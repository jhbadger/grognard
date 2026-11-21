"""The Kivy front end, for the Android app (where there is no Tk) or for
anyone who asks for it with --kivy.  Like the Tk one it only shows the
game's framebuffer, scaled to fit, and passes on keys and taps."""

import importlib
import os

W, H = 640, 480

ANDROID = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ

# Kivy's key codes, as the game names them (27 is also Android's Back).
KEYS = {273: 'up', 274: 'down', 276: 'left', 275: 'right', 13: 'enter',
        271: 'enter', 27: 'esc', 8: 'backspace', 127: 'backspace',
        32: 'space', 9: 'tab', 282: 'f1'}


def kivy(module):
    """A Kivy module.  Pydroid decides how to run a script from the modules
    it imports, so the name is put together at run time: the games must be
    started as Tk apps there."""
    return importlib.import_module('ki' + 'vy' + module)


class KivyShell:
    def __init__(self, game, width=1280, height=800):
        os.environ.setdefault('KIVY_NO_ARGS', '1')
        os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
        config = kivy('.config').Config
        config.set('kivy', 'exit_on_escape', '0')       # Esc and Back: ours
        config.set('kivy', 'log_level', 'warning')
        if ANDROID:
            config.remove_option('input', 'mouse')
        else:
            config.set('input', 'mouse',
                       'mouse,disable_multitouch,disable_on_activity')
            config.set('graphics', 'width', str(width))
            config.set('graphics', 'height', str(height))
        self.g = game
        self.Window = kivy('.core.window').Window
        self.Clock = kivy('.clock').Clock
        self.Texture = kivy('.graphics.texture').Texture
        self.graphics = kivy('.graphics')
        self.App = kivy('.app').App
        self.Widget = kivy('.uix.widget').Widget
        self.app = None

    # ------------------------------------------------------------ drawing

    def build_root(self):
        shell = self
        g = self.g
        self.fsize = (W, H)
        tex = self.make_texture(W, H)
        gr = self.graphics

        class Screen(self.Widget):
            def on_touch_down(self, touch):
                x, y = shell.to_game(touch.x, touch.y)
                if 0 <= x < shell.fsize[0] and 0 <= y < shell.fsize[1]:
                    g.press(x, y)
                    touch.ud['grognard'] = True
                return True

            def on_touch_move(self, touch):
                if touch.ud.get('grognard'):
                    g.drag(*shell.to_game(touch.x, touch.y))
                    if g.dirty:
                        shell.draw()
                return True

            def on_touch_up(self, touch):
                if touch.ud.get('grognard'):
                    touch.ud['grognard'] = False
                    g.release(*shell.to_game(touch.x, touch.y))
                    shell.after_input()
                return True

        root = Screen()
        with root.canvas:
            gr.Color(0, 0, 0, 1)
            self.back = gr.Rectangle(pos=(0, 0), size=self.Window.size)
            gr.Color(1, 1, 1, 1)
            self.rect = gr.Rectangle(texture=tex, pos=(0, 0), size=(W, H))
        self.root = root
        self.fit()
        return root

    def make_texture(self, w, h):
        tex = self.Texture.create(size=(w, h), colorfmt='rgb')
        tex.mag_filter = tex.min_filter = 'nearest'
        tex.flip_vertical()             # Kivy counts rows from the bottom
        self.tex = tex
        return tex

    def fit(self, *args):
        ww, wh = self.Window.size
        # an upright window (a phone held upright) gets the upright layout
        self.g.portrait = wh > ww * 1.05
        W, H = self.fsize
        s = min(ww / W, wh / H)
        # whole pixels look crisper when the screen is big enough for them
        if s >= 2:
            s = int(s * 2) / 2
        self.scale = s
        self.ox = (ww - W * s) / 2
        self.oy = (wh - H * s) / 2
        self.back.size = (ww, wh)
        self.rect.pos = (self.ox, self.oy)
        self.rect.size = (W * s, H * s)
        self.g.dirty = True

    def to_game(self, tx, ty):
        """Kivy's point (from the bottom left) to the game's pixel."""
        x = int((tx - self.ox) / self.scale)
        y = int(self.fsize[1] - (ty - self.oy) / self.scale)
        return x, y

    def draw(self):
        s = self.g.frame()
        if (s.w, s.h) != self.fsize:
            self.fsize = (s.w, s.h)
            self.rect.texture = self.make_texture(s.w, s.h)
            self.fit()
        self.tex.blit_buffer(bytes(s.buf), colorfmt='rgb', bufferfmt='ubyte')
        self.root.canvas.ask_update()

    # -------------------------------------------------------------- input

    def key_down(self, window, key, scancode, codepoint, modifiers):
        if key in KEYS:
            k = KEYS[key]
        elif codepoint and codepoint.isprintable():
            k = codepoint
            if 'shift' in modifiers and k.isalpha():
                k = k.upper()
        else:
            return False
        if len(k) == 1 and k.isalpha():
            k = k.lower()
        self.g.key(k)
        self.after_input()
        return True

    def after_input(self):
        if self.g.quit:
            self.close()
            return
        self.draw()

    def tick(self, dt):
        self.g.update(dt)
        if self.g.quit:
            self.close()
            return
        if self.g.dirty:
            self.draw()

    # ---------------------------------------------------------------- run

    def close(self):
        g = self.g
        if not g.quit and not g.e.over:
            g.save()
        g.sound.stop()
        if self.app:
            self.app.stop()

    def run(self):
        shell = self
        g = self.g

        class GrognardApp(self.App):
            title = g.title

            def build(app):
                root = shell.build_root()
                shell.Window.bind(on_key_down=shell.key_down)
                shell.Window.bind(on_resize=shell.fit)
                shell.Window.bind(on_request_close=lambda *a, **k:
                                  (shell.close(), True)[1])
                shell.Clock.schedule_interval(shell.tick, 1 / 30)
                # a phone's window comes up at its size without a resize
                shell.Clock.schedule_once(shell.fit, 0)
                return root

            def on_pause(app):
                """Switched away from: Android may close the app without
                another word, so the game is saved now."""
                if not g.e.over:
                    g.save()
                g.sound.stop()
                return True

            def on_resume(app):
                g.dirty = True

        self.app = GrognardApp()
        try:
            icon = getattr(g, 'icon_path', None)
            if icon:
                self.app.icon = icon
        except Exception:
            pass
        self.app.run()
