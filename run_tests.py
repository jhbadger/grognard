#!/usr/bin/env python3
"""Run every test: the engine's, then each game's, each game in its own
Python.

    ./run_tests.py              everything
    ./run_tests.py --long       fuzz 30 random games per game, not 3
    ./run_tests.py --no-gui     skip the tests that open windows
    ./run_tests.py crossroads   just one game (and the engine)

Set KIVY_PYTHON to a Python with Kivy installed to test the Kivy window
too.
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tests'))


def main(args):
    import util
    env = dict(os.environ)
    if '--long' in args:
        env['GROGNARD_FUZZ'] = '30'
    if '--no-gui' in args:
        env['GROGNARD_NO_GUI'] = '1'
    names = [a for a in args if not a.startswith('--')] or util.games()
    runs = [('engine', ['test_engine'], {})]
    for name in names:
        runs.append((name, ['test_game', 'test_shells'],
                     {'GROGNARD_GAME': name}))
    failed = []
    for label, modules, extra in runs:
        start = time.time()
        e = dict(env, **extra)
        p = subprocess.run([sys.executable, '-m', 'unittest', '-q'] + modules,
                           cwd=os.path.join(HERE, 'tests'), env=e,
                           capture_output=True, text=True)
        tail = p.stderr.strip().splitlines()
        summary = tail[-1] if tail else ''
        print('%-12s %-30s %5.1fs' % (label, summary, time.time() - start))
        if p.returncode != 0:
            failed.append(label)
            print(p.stderr)
    print('FAILED: ' + ', '.join(failed) if failed else 'All tests passed.')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
