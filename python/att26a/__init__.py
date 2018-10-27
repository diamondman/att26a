#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""
    __init__.py
    ~~~~~~~~~~~

    AT&T 26A Direct Extension Selector Console Driver.

    :copyright: (c) 2018 by Jessy Diamond Exum.
    :license: see LICENSE for more details.
"""

__title__ = 'att26a'
__version__ = '0.0.1'
__author__ = 'Jessy Diamond Exum'

__ALL__ = ['LED_OFF',
           'LED_BLINK1',
           'LED_BLINK2',
           'LED_ON',
           'LED_MODES',
           'ATT26A']

import serial
import threading
import time
import queue
import math

LED_OFF = 0x0
LED_BLINK1 = 0x8
LED_BLINK2 = 0xD
LED_ON = 0xF

LED_MODES = (LED_OFF, LED_BLINK1, LED_BLINK2, LED_ON)

MSG_KA = 0xFF # Keep Alive
MSG_ACK = 0xFD # Acknowledge

class ATT26A(object):
    """AT&T 26A Direct Extension Selector Console Driver.

    Provides functions to read button presses and set led states on
    AT&T 26A hardware.

    Args:
        devname (str): A path to a posix character device.
        verbose (:obj:`bool`, optional): Enable verbose output.
    """

    def __init__(self, devname, *, verbose=False):
        self._verbose = verbose
        self._ser = ATT26A._open_dev(devname)
        self.reset()
        self._btnq = queue.Queue(100)
        self.__do_recvthread = True
        self._recvthread = threading.Thread(daemon=True, target=self.__recvthread_func)
        self._recvthread.start()

    def __recvthread_func(self):
        while(self.__do_recvthread):
            data = self._ser.read(1) # Blocks
            if data[0] in (MSG_KA, MSG_ACK):
                continue
            new_btn = ATT26A._shift7_right(data[0])

            if self._verbose:
                print("%s (%d) => %s (%d)" % (hex(data[0])[2:].zfill(2), data[0],
                                              hex(new_btn)[2:].zfill(2), new_btn))

            self._btnq.put(new_btn)

    def get_btn_press(self, block=True, timeout=None):
        """Read a single button press off of the button event queue.

        Currently, the 'block' and 'timeout' parameters are passed
        directly to queue.Queue.get. Consult the appropriate
        documentation for their functions.

        """
        return self._btnq.get(block=block, timeout=timeout)

    def reset(self):
        """Execute a complete power on reset of the 26A."""
        self._ser.dtr = False
        time.sleep(0.1)
        self._ser.dtr = True

    @staticmethod
    def __prepare_msg_frame(msg):
        if len(msg) > 15:
            raise ValueError("msg may not be longer than 15 bytes.")
        h = 0x7F
        for b in msg[1:]:
            h ^= b
        return msg + bytes([h]) + b'\xff'

    def _tx(self, msg):
        if len(msg) == 0:
            raise ValueError("Message must be at least one byte long.")
        if len(msg) >= 16:
            raise ValueError("Message must be shorter than 16 bytes.")
        if b'\xFF' in msg:
            raise ValueError("Message may not contain a byte of value 0xFF.")

        outmsg = ATT26A.__prepare_msg_frame(msg)
        if(self._verbose):
            print(":".join((hex(b)[2:] for b in outmsg)))
        self._ser.write(outmsg)

    def set_led_range_state(self, start_ledid, states_on_off):
        """Set a range of LEDs on the 26A arbitrarily to ON or OFF (no blink).

        Starting at LED ID 'start_ledid', set an LED state to ON or
        OFF for each value in the 'states_of_off' array (True means
        ON, False means OFF). This function only works on LEDs 0 to
        99, and excludes the botton two special button rows.

        If 'start_ledid' plus the length of 'states_on_off' exceed the
        max LED ID (99), the operation continues, but wraps back
        around to led 0.

        There is a maximum of 77 LED states that can be written in one
        message. And for hardware obfuscations (thank AT&T), a length
        of 71 LED states is not supported.

        Args:
            start_ledid (int): ID of first LED in the range.
            code (:obj:`list` of :obj:`bool`): List of states to
                set. Max length 77. Length 71 unsupported.

        """
        
        if start_ledid > 99 or start_ledid < 0:
            raise ValueError("start_ledid must be between 0 and 99; not %d" % start_ledid)

        num_leds = len(states_on_off)
        if num_leds == 0:
            raise ValueError("states_on_off can not be empty.")
        if num_leds == 71:
            raise ValueError("The device does not support setting 71 leds at once. Either send "
                             "multiple requests, or write 72 or more values.")
        if num_leds > 77:
            raise ValueError("Only up to 77 leds may be set at a time, not %d" % num_leds)

        if num_leds != 70:
            num_leds -= 1

        data = bytearray(math.ceil(len(states_on_off)/7.00))
        # Top bit always 0, up to 7 leds per byte, high bit to low bit.
        for i, val in enumerate(states_on_off):
            data[i//7] |= (bool(val) << (6-(i%7)))

        self._tx(b'\x85\x07' + bytes([ATT26A._shift7_left(start_ledid),
                                      num_leds]) + data)

    def set_led_state(self, state, ledID):
        """Set an individual LED on the 26A to one of 4 supported states.

        Args:
            state: (int): The state for the selected LED to assume.
                Supports att26a.LED_OFF, att26a.LED_BLINK1,
                att26a.LED_BLINK2, and att26a.LED_ON.
            ledID (int): ID of the LED to set the state of.

        """
        if state not in (LED_OFF, LED_BLINK1, LED_BLINK2, LED_ON): #translates to 0-3
            raise ValueError("state can either be 0x0, 0x8, 0xD, or 0xF, not %s" % hex(state))
        if ledID >= 120:
            raise ValueError("ledID must be smaller than 120; not %d." % ledID)

        self._tx(b'\x85' + bytes([0x20 | state, ATT26A._shift7_left(ledID)]))

    def set_led_off(self, ledID):
        """Set an individual LED on the 26A to the OFF state.

        Args:
            ledID (int): ID of the LED to set the state of.
        """
        self.set_led_state(LED_OFF, ledID)

    def set_led_blink1(self, ledID):
        """Set an individual LED on the 26A to the BLINK1 state.

        Args:
            ledID (int): ID of the LED to set the state of.
        """
        self.set_led_state(LED_BLINK1, ledID)

    def set_led_blink2(self, ledID):
        """Set an individual LED on the 26A to the BLINK2 state.

        Args:
            ledID (int): ID of the LED to set the state of.
        """
        self.set_led_state(LED_BLINK2, ledID)

    def set_led_on(self, ledID):
        """Set an individual LED on the 26A to the ON state.

        Args:
            ledID (int): ID of the LED to set the state of.
        """
        self.set_led_state(LED_ON, ledID)

    def set_factory_test_mode_enable(self, enable):
        """Enable or disable the factory test mode.

        The factory test mode blinks rows of LEDs on the 26A, and is
        good to quickly check if all the LEDs are working correctly.

        While factory test mode is on, LED states can be set, but they
        will not be displayed on the 26A until factory test mode is
        disabled.

        Args:
            enable (bool): Weather to turn factory test mode on.

        """
        if enable:
            self._tx(b'\x85\x10\x6F')
        else:
            self._tx(b'\x85\x30\x4F')

    def set_IO_enable(self, enable):
        """Enable or disable the 26A's IO controller (default on after reset).

        The 26A's IO controller handles powering LEDs, and reading
        button presses. If disabled, the controller will not power any
        LEDs, or detect any button presses.

        While the IO controller is disabled, LED states can be set
        (but they will not be displayed on the 26A until the IO
        controller is enabled), and button presses will be ignored
        completely (Button presses that occured while the IO contoller
        was disabled will not be reported once the IO controller is
        re-enabled).

        Args:
            enable (bool): Weather to enable or disable the IO contoller.

        """
        if enable:
            self._tx(b'\x85\x40\x3F')
        else:
            self._tx(b'\x85\x50\x2F')

    # Read the led state of any led from 200 to 120. Returns 1 or 2
    # bytes. This function is not even that useful, as it only works
    # for the bottom 20 lights.  Since this is the only function that
    # returns a value, and it is useless, there is no need to handle
    # return values. Just keep a local buffer if you need to track the
    # led state.
    #def get_high_led_status(ser, XX):
    #    # A520:XX
    #    if 100 > XX or XX >= 120:
    #        raise ValueError("XX must be 100 <= XX < 120; not %d" % XX)
    #
    #    tx(ser, b'\xA5\x20' + bytes([ATT26A._shift7_left(XX)]))

    @staticmethod
    def _open_dev(devname):
        return serial.Serial(devname, baudrate=10752, #write_timeout=(100/1000),
                             bytesize=serial.EIGHTBITS, parity=serial.PARITY_ODD,
                             stopbits=serial.STOPBITS_ONE)

    @staticmethod
    def _shift7_left(b):
        return ((b << 1) & 0x7E) | ((b & 0x40) >> 6)

    @staticmethod
    def _shift7_right(b):
        return ((b & 0x7E) >> 1) | ((b & 0x01) << 6)
