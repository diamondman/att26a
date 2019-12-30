#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def light_bright(devname):
    import att26a
    import signal

    with att26a.ATT26A(devname) as led_board:
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
            except att26a.DriverClosedError as e:
                break

if __name__ == "__main__":
    from att26a.clihelper import setup_standard_demo_cli
    setup_standard_demo_cli('Basic Light Bright', light_bright)
