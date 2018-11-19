#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory
import att26a

def raw_animation2(devname, verbose):
    import signal
    import time

    frame = (True, False, False, True, True, False, False, True, True, False,
             False, True, True, False, False, True, True, False, False, True)*5
    
    with att26a.ATT26A(devname, verbose=verbose) as led_board:
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
    import argparse
    parser = argparse.ArgumentParser(description='Display one frame, but offset it over time.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')

    args = parser.parse_args()
    try:
        raw_animation2(args.devname, args.verbose)
    except att26a.CanNotOpenDeviceError as e:
        print("ERROR:", str(e))
        exit(1)
