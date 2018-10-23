#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def random_noise2(devname, verbose):
    import random
    import att26a
    led_board = att26a.ATT26A(devname, verbose=verbose)
    led_map = [False] * 120
    
    while True:
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
