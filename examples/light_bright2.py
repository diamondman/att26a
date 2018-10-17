#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def light_bright2(devname, verbose):
    import att26a
    led_board = att26a.ATT26A(devname, verbose=verbose)
    mode = 3

    led_board.set_led_state(att26a.LED_OFF, 100)
    led_board.set_led_state(att26a.LED_BLINK1, 101)
    led_board.set_led_state(att26a.LED_BLINK2, 102)
    led_board.set_led_state(att26a.LED_ON, 103)

    while True:
        btn = led_board.get_btn_press()
        if btn >= 0 and btn <= 99:
            #btn_map[btn] = mode
            led_board.set_led_state(att26a.LED_MODES[mode], btn)
        elif btn == 119:
            for i in range(0, 100):
                led_board.set_led_state(att26a.LED_MODES[mode], i)
        elif btn == 100:
            mode = 0
        elif btn == 101:
            mode = 1
        elif btn == 102:
            mode = 2
        elif btn == 103:
            mode = 3

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Better Light Bright')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    light_bright2(args.devname, args.verbose)
