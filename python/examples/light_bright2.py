#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory
import att26a

def light_bright2(devname, verbose):
    import signal

    with att26a.ATT26A(devname, verbose=verbose) as led_board:
        def signal_handler(sig, frame):
            led_board.close()
        signal.signal(signal.SIGINT, signal_handler)

        led_board.set_led_state(att26a.LED_OFF, 100)
        led_board.set_led_state(att26a.LED_BLINK1, 101)
        led_board.set_led_state(att26a.LED_BLINK2, 102)
        led_board.set_led_state(att26a.LED_ON, 103)

        mode = 3
        while led_board.is_open:
            try:
                btn = led_board.get_btn_press()
                if btn >= 0 and btn <= 99:
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
            except att26a.DriverShuttingDownError as e:
                break

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Better Light Bright')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    try:
        light_bright2(args.devname, args.verbose)
    except att26a.CanNotOpenDeviceError as e:
        print("ERROR:", str(e))
        exit(1)
