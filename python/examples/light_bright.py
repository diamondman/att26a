#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def light_bright(devname, verbose):
    import att26a
    led_board = att26a.ATT26A(devname, verbose=verbose)
    led_map = [False] * 120

    while True:
        btn = led_board.get_btn_press()
        print(btn)
        led_map[btn] = not led_map[btn]
        state = att26a.LED_ON if led_map[btn] else att26a.LED_OFF
        led_board.set_led_state(state, btn)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Basic Light Bright')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    light_bright(args.devname, args.verbose)
