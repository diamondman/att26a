#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def random_noise2(devname, verbose):
    import att26a
    import random
    import signal
    import threading

    breakloop = threading.Event()
    def signal_handler(sig, frame):
        breakloop.set()
    signal.signal(signal.SIGINT, signal_handler)

    with att26a.ATT26A(devname, verbose=verbose) as led_board:
        led_map = [False] * 120

        while not breakloop.is_set():
            led = random.randint(0, len(led_map)-1)
            led_map[led] = not led_map[led]
            state = att26a.LED_ON if led_map[led] else att26a.LED_OFF
            led_board.set_led_state(state, led)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Light up random leds')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    print("NAME:", repr(args.devname))
    random_noise2(args.devname, args.verbose)
