"""Synthesized sound effects, written once as WAV files and played with
whatever the system has: afplay on macOS, paplay or aplay on Linux,
Android's MediaPlayer through pyjnius or pygame's mixer (Pydroid), or
winsound on Windows.  With none of these the game is silent.  The
effects are cached in ~/.cache/<game>.  (The players are blobber's.)"""

import math
import os
import random
import shutil
import struct
import subprocess
import sys
import wave

RATE = 22050
def _env(n, attack=0.005, release=0.08):
    a = max(1, int(attack * RATE))
    r = max(1, int(release * RATE))
    out = []
    for i in range(n):
        v = 1.0
        if i < a:
            v = i / a
        if i > n - r:
            v = min(v, (n - i) / r)
        out.append(v)
    return out


def tone(freq, dur, wave_='square', vol=0.3, slide=0.0, duty=0.5):
    n = int(dur * RATE)
    env = _env(n)
    out = []
    ph = 0.0
    for i in range(n):
        f = freq + slide * i / n
        ph += f / RATE
        p = ph % 1.0
        if wave_ == 'square':
            v = 1.0 if p < duty else -1.0
        elif wave_ == 'tri':
            v = 4 * abs(p - 0.5) - 1
        elif wave_ == 'saw':
            v = 2 * p - 1
        else:
            v = math.sin(2 * math.pi * p)
        out.append(v * vol * env[i])
    return out


def noise(dur, vol=0.3, decay=6.0, seed=1, lowpass=0.5):
    rng = random.Random(seed)
    n = int(dur * RATE)
    out = []
    last = 0.0
    for i in range(n):
        v = rng.uniform(-1, 1)
        last = last + (v - last) * lowpass
        out.append(last * vol * math.exp(-decay * i / n))
    return out


def hooves(strides=3):
    """A horse at a canter: hollow knocks on hard ground, three beats
    to a stride and a pause."""
    out = []
    for s in range(strides):
        for b in range(3):
            k = s * 3 + b
            clop = mixdown(noise(0.03, 0.25, 16, k, 0.3),
                           tone(480 - 40 * b, 0.04, 'sine', 0.3, -150))
            out += clop + [0.0] * int(RATE * 0.06)
        out += [0.0] * int(RATE * 0.12)
    return out


def seq(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def mixdown(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


EFFECTS = {
    'click':  lambda: tone(880, 0.03, 'square', 0.1, duty=0.25),
    'select': lambda: seq(tone(660, 0.03, 'square', 0.12, duty=0.25),
                          tone(990, 0.04, 'square', 0.12, duty=0.25)),
    'move':   lambda: seq(*[noise(0.05, 0.25, 8, k, 0.12) + [0.0] * 600
                            for k in range(3)]),
    'tracks': lambda: mixdown(seq(*[noise(0.04, 0.3, 5, k, 0.3) + [0.0] * 300
                                    for k in range(6)]),
                              tone(55, 0.42, 'saw', 0.12)),
    'hooves': lambda: hooves(),
    'gun':    lambda: mixdown(noise(0.5, 0.6, 7, 4, 0.35),
                              tone(70, 0.35, 'sine', 0.5, -40)),
    'boom':   lambda: mixdown(noise(0.9, 0.7, 4, 7, 0.2),
                              tone(50, 0.8, 'sine', 0.6, -30)),
    'rifle':  lambda: seq(*[noise(0.06, 0.4, 12, k, 0.7) + [0.0] * 1200
                            for k in range(5)]),
    'lose':   lambda: tone(300, 0.6, 'square', 0.15, -220, 0.3),
    'bugle':  lambda: seq(*[tone(392 * 2 ** (k / 12), d, 'square', 0.18,
                                 duty=0.3)
                            for k, d in ((0, .12), (5, .12), (9, .12),
                                         (12, .3), (9, .12), (12, .45))]),
    'turn':   lambda: seq(tone(523, 0.08, 'tri', 0.3), tone(784, 0.14, 'tri',
                                                            0.3)),
    'nope':   lambda: seq(tone(200, 0.08, 'square', 0.15),
                          tone(150, 0.12, 'square', 0.15)),
}
def write_wav(path, samples):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 32000))
                               for s in samples))


ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ


# Players.  Each starts a WAV file and returns a handle that, like a
# subprocess, has poll() (None while it plays) and terminate().

class CommandPlayer:
    """A command-line player: afplay, paplay or aplay."""
    music = True

    def __init__(self, cmd):
        self.cmd = cmd

    def start(self, path):
        return subprocess.Popen(self.cmd + [path], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

    @classmethod
    def find(cls):
        for cmd in (['afplay'], ['paplay'], ['aplay', '-q']):
            if shutil.which(cmd[0]):
                return cls(cmd)
        return None


class MediaPlayer:
    """Android's android.media.MediaPlayer, through pyjnius (pip install
    pyjnius in Pydroid)."""
    music = True

    class Handle:
        def __init__(self, mp):
            self.mp = mp

        def poll(self):
            if self.mp is None:
                return 0
            try:
                if self.mp.isPlaying():
                    return None
            except Exception:
                pass
            self.terminate()
            return 0

        def terminate(self):
            if self.mp is not None:
                try:
                    self.mp.stop()
                except Exception:
                    pass
                self.mp.release()
                self.mp = None

    def __init__(self, cls):
        self.cls = cls

    def start(self, path):
        mp = self.cls()
        try:
            mp.setDataSource(path)
            mp.prepare()
            mp.start()
        except Exception as e:
            mp.release()
            raise OSError(str(e))
        return self.Handle(mp)

    @classmethod
    def find(cls):
        try:
            import importlib
            jnius = importlib.import_module('jnius')
            return cls(jnius.autoclass('android.media.MediaPlayer'))
        except Exception:
            return None


class MixerPlayer:
    """SDL's mixer, through pygame.  Pydroid chooses how to run a script
    from the modules it imports, so the module's name is put together at
    run time: a Tk game must not be started as an SDL one."""
    music = True

    class Handle:
        def __init__(self, channel, snd):
            self.channel, self.snd = channel, snd

        def poll(self):
            ch = self.channel
            if ch and ch.get_busy() and ch.get_sound() is self.snd:
                return None
            return 0

        def terminate(self):
            if self.poll() is None:
                self.channel.stop()

    def __init__(self, mixer):
        self.mixer = mixer
        self.sounds = {}

    def start(self, path):
        snd = self.sounds.get(path)
        if snd is None:
            try:
                snd = self.sounds[path] = self.mixer.Sound(path)
            except Exception as e:
                raise OSError(str(e))
        return self.Handle(snd.play(), snd)

    @classmethod
    def find(cls):
        try:
            import importlib
            os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
            mixer = importlib.import_module('py' + 'game.mixer')
            mixer.init(RATE, -16, 1, 512)
            mixer.set_num_channels(8)
            return cls(mixer)
        except Exception:
            return None


class WinsoundPlayer:
    """Windows' winsound: one sound at a time, so effects only."""
    music = False

    class Handle:
        def poll(self):
            return 0

        def terminate(self):
            pass

    def __init__(self, ws):
        self.ws = ws

    def start(self, path):
        self.ws.PlaySound(path, self.ws.SND_FILENAME | self.ws.SND_ASYNC)
        return self.Handle()

    @classmethod
    def find(cls):
        if not sys.platform.startswith('win'):
            return None
        try:
            import winsound
            return cls(winsound)
        except ImportError:
            return None


def find_player():
    player = CommandPlayer.find()
    if not player and ANDROID:
        player = MediaPlayer.find()
    return player or WinsoundPlayer.find() or MixerPlayer.find()


class Sound:
    def __init__(self, game_id):
        self.on = True
        from . import home_dir
        self.dir = os.path.join(home_dir(), '.cache', game_id)
        self.player = find_player()
        self.procs = []
        self.ready = set()

    @property
    def available(self):
        return self.player is not None

    def path(self, name):
        return os.path.join(self.dir, name + '.wav')

    def prepare(self):
        if not self.available:
            return
        try:
            os.makedirs(self.dir, exist_ok=True)
            for name, fn in EFFECTS.items():
                p = self.path(name)
                if not os.path.exists(p):
                    write_wav(p, fn())
                self.ready.add(name)
        except OSError:
            self.player = None

    def play(self, name):
        """Play an effect, unless too many are still going: if the system's
        audio is stuck, players never exit, and they must not pile up."""
        if not self.on or name not in self.ready or not self.player:
            return
        self.procs = [h for h in self.procs if h.poll() is None]
        if len(self.procs) >= 4:
            return
        try:
            self.procs.append(self.player.start(self.path(name)))
        except OSError:
            pass

    def stop(self):
        for h in self.procs:
            try:
                h.terminate()
            except OSError:
                pass
        self.procs = []


class Silent:
    """No sound at all (tests, screenshots, the self-test)."""
    on = False
    available = False

    def play(self, name):
        pass

    def stop(self):
        pass
