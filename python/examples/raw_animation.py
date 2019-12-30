#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def raw_animation(devname):
    import att26a
    import signal
    import time

    frames = (
        ((False, True)*5 + (True, False)*5)*5,
        ((True, False)*5 + (False, True)*5)*5,
        ((True, False, False, True)*5)*5,
        ((False, True, True, False)*5)*5,
        ((True, True, False, False)*5)*5,
        ((False, False, True, True)*5)*5,
    )
    with att26a.ATT26A(devname) as led_board:
        def signal_handler(sig, frame):
            led_board.close()
        signal.signal(signal.SIGINT, signal_handler)

        while led_board.is_open:
            try:
                for frame in frames:
                    led_board.set_led_range_state(0, frame);
                    time.sleep(0.1)
            except att26a.DriverClosedError as e:
                break

if __name__ == "__main__":
    from att26a.clihelper import setup_standard_demo_cli
    setup_standard_demo_cli('Play an animation of several frames.', raw_animation)
