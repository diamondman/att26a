#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def random_noise3(devname):
    import att26a
    import random
    import signal

    with att26a.ATT26A(devname) as led_board:
        def signal_handler(sig, frame):
            led_board.close()
        signal.signal(signal.SIGINT, signal_handler)

        while led_board.is_open:
            try:
                led_state = [random.choice((False, True)) for i in range(100)]
                led_board.set_led_range_state(0, led_state)
            except att26a.DriverClosedError as e:
                break

if __name__ == "__main__":
    from att26a.clihelper import setup_standard_demo_cli
    setup_standard_demo_cli('Randomly set all lights ON/OFF at once.', random_noise3)
