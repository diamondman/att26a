#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def random_noise(devname, verbose):
    import random
    import att26a
    led_board = att26a.ATT26A(devname, verbose=verbose)
    
    while True:
        led = random.randint(0, 119)
        state = random.choice((att26a.LED_OFF, att26a.LED_ON))
        led_board.set_led_state(state, led)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Light up random leds')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    print("NAME:", repr(args.devname))
    random_noise(args.devname, args.verbose)
