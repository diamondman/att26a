#!/usr/bin/env python3

import sys
from os.path import dirname, join
sys.path.append(join(dirname(__file__), "..")) # Enable importing from parent directory

def light_bright2(devname):
    import att26a
    import signal

    with att26a.ATT26A(devname) as led_board:
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
            except att26a.DriverClosedError as e:
                break

if __name__ == "__main__":
    from att26a.clihelper import setup_standard_demo_cli
    setup_standard_demo_cli('Better Light Bright', light_bright2)
