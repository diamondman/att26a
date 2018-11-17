#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory
import att26a

def light_bright(devname, verbose):
    import signal

    with att26a.ATT26A(devname, verbose=verbose) as led_board:
        def signal_handler(sig, frame):
            led_board.close()
        signal.signal(signal.SIGINT, signal_handler)

        led_map = [False] * 120
        while led_board.is_open:
            try:
                btn = led_board.get_btn_press()
                led_map[btn] = not led_map[btn]
                state = att26a.LED_ON if led_map[btn] else att26a.LED_OFF
                led_board.set_led_state(state, btn)
            except att26a.DriverShuttingDownError as e:
                break

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Basic Light Bright')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    try:
        light_bright(args.devname, args.verbose)
    except att26a.CanNotOpenDeviceError as e:
        print("ERROR:", str(e))
        exit(1)
