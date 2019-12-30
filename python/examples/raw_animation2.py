#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def raw_animation2(devname):
    import att26a
    import signal
    import time

    frame = (True, False, False, True, True, False, False, True, True, False,
             False, True, True, False, False, True, True, False, False, True)*5

    with att26a.ATT26A(devname) as led_board:
        def signal_handler(sig, frame):
            led_board.close()
        signal.signal(signal.SIGINT, signal_handler)

        i = 0
        while led_board.is_open:
            try:
                led_board.set_led_range_state(i, frame);
                i = (i + 1)%100
            except att26a.DriverClosedError as e:
                break

if __name__ == "__main__":
    from att26a.clihelper import setup_standard_demo_cli
    setup_standard_demo_cli('Display one frame, but offset it over time.', raw_animation2)
