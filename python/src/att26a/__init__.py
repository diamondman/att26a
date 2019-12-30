#!/usr/bin/env python3
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

__ALL__ = [
    'LED_OFF',
    'LED_BLINK1',
    'LED_BLINK2',
    'LED_ON',
    'LED_MODES',
    'ATT26A',
    'DriverClosedError',
    'DriverShuttingDownError',
    'Att26AProtocolError',
    'CommandTimeoutError',
    'IncorrectResponseError',
    'Att26AIOError',
    'CanNotOpenDeviceError',
    'ButtonTimeoutError',
]

import serial
import threading
import time
import queue
import math
import logging

from . import interruptablequeue

LED_OFF = 0x0
LED_BLINK1 = 0x8
LED_BLINK2 = 0xD
LED_ON = 0xF

LED_MODES = (LED_OFF, LED_BLINK1, LED_BLINK2, LED_ON)

MSG_KA = 0xFF # Keep Alive
MSG_ACK = 0xFD # Acknowledge

class Att26AError(Exception):
    pass

# Driver State Unusable Exceptions
class DriverClosedError(Att26AError):
    pass

class DriverShuttingDownError(DriverClosedError):
    pass

# Protocol Exceptions
class Att26AProtocolError(Att26AError):
    pass

class CommandTimeoutError(Att26AProtocolError):
    pass

class IncorrectResponseError(Att26AProtocolError):
    pass

# Other Exceptions
class Att26AIOError(Att26AError):
    pass

class CanNotOpenDeviceError(Att26AError):
    pass

class ButtonTimeoutError(Att26AError):
    pass

class ATT26A(object):
    """AT&T 26A Direct Extension Selector Console Driver.

    Provides functions to read button presses and set led states on
    AT&T 26A hardware.

    Args:
        devname (str): A path to a posix character device.
        log (:obj:`logging.Logger`, optional): logging object.
    """

    def __init__(self, dev, *, log=None):
        self.__is_open = True
        self.__do_recvthread = False
        self.__recvthread = None
        self.__btnq = None
        self.__retq = None

        self._log = logging.getLogger('att26a') if not log else log

        if isinstance(dev, str):
            self.__ser = ATT26A.openSerialPortByName(dev)
            self._log.info("%s (type: %s)", self.__ser, type(self.__ser))
        else:
            self.__ser = dev

        self.reset()

    def __enter__(self):
        if not self.__is_open:
            raise DriverClosedError("This device is already closed, create a new one instead "
                                    "of re-opening this one.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._close()

    def _close(self, *, dojoin=True):
        if self.__is_open:
            self.__do_recvthread = False
            self.__retq.interrupt_all_consumers()
            self.__btnq.interrupt_all_consumers()
            if dojoin:
                self.__recvthread.join(0.5)
            self.__ser.close()
        self.__is_open = False

    def reset(self):
        """Execute a complete power on reset of the 26A."""

        # Force the device into reset
        self.__ser.dtr = False
        time.sleep(0.1)

        # Terminate the reader thread
        self.__do_recvthread = False
        if self.__recvthread is not None:
            self.__recvthread.join(2)

        # Clear out the queues
        self.__btnq = interruptablequeue.InterruptableQueue(100)
        self.__retq = interruptablequeue.InterruptableQueue()

        # Exit device reset
        self.__ser.dtr = True

        # (Re)start the reader thread
        self.__do_recvthread = True
        self.__recvthread = threading.Thread(daemon=True, target=self.__recvthread_func)
        self.__recvthread.start()


    def __recvthread_func(self):
        retdata = bytearray()
        while(self.__do_recvthread):
            try:
                data_raw = self.__ser.read(1) # Blocks
            except serial.serialutil.SerialException as e:
                self._log.error("ATT26A closing due to exception on receiver thread: '%s'" % e)
                self._close(dojoin=False)
                break

            data = data_raw[0] #TODO: Should check length first?
            try:
                if (data & 0x80) == 0x00:
                    self._handle_button_press(ATT26A._shift7_right(data))
                elif data == MSG_KA:
                    pass #TODO: maybe detect hardware timeout?
                elif data == MSG_ACK:
                    self._log.debug("retdata: " + ':'.join('{:02x}'.format(x) for x in retdata))
                    self.__retq.put(bytes(retdata))
                    retdata.clear()
                else:
                    retdata.append(data)
            except DriverShuttingDownError as e:
                self._log.error("Att26A receiver thread terminating due to DriverShuttingDownError")
                break

    def _handle_button_press(self, id):
        self._log.info("%s btn %d pressed." % (type(self).__name__, id))

        self.__btnq.put(id)

    @staticmethod
    def __prepare_msg_frame(msg):
        if len(msg) > 15:
            raise ValueError("msg may not be longer than 15 bytes.")
        h = 0x7F
        for b in msg[1:]:
            h ^= b
        return msg + bytes([h]) + b'\xff'

    def _tx(self, msg):
        if not self.is_open:
            raise DriverClosedError()

        if len(msg) == 0:
            raise ValueError("Message must be at least one byte long.")
        if len(msg) >= 16:
            raise ValueError("Message must be shorter than 16 bytes.")
        if b'\xFF' in msg:
            raise ValueError("Message may not contain a byte of value 0xFF.")

        outmsg = ATT26A.__prepare_msg_frame(msg)
        self._log.debug("TX:" + ":".join((hex(b)[2:] for b in outmsg)))

        try:
            self.__ser.write(outmsg)
        except serial.SerialTimeoutException as e:
            raise CommandTimeoutError("Timeout sending message.")
        except serial.serialutil.SerialException as e:
            raise Att26AIOError()

        try:
            return self.__retq.get(block=True, timeout=0.1)
        except queue.Empty:
            raise CommandTimeoutError("Timeout waiting for response.")
        except interruptablequeue.QueueInterruptException as e:
            raise DriverShuttingDownError()

    def get_btn_press(self, block=True, timeout=None):
        """Read a single button press off of the button event queue.

        Currently, the 'block' and 'timeout' parameters are passed
        directly to queue.Queue.get. Consult the appropriate
        documentation for their functions.
        """
        try:
            return self.__btnq.get(block=block, timeout=timeout)
        except queue.Empty as e:
            raise ButtonTimeoutError()
        except interruptablequeue.QueueInterruptException as e:
            raise DriverShuttingDownError()

    def _set_led_range_state_raw(self, start_ledid, states_on_off):
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

    def set_led_range_state(self, start_ledid, states_on_off):
        """Set a range of LEDs on the 26A arbitrarily to ON or OFF (no blink).

        Starting at LED ID 'start_ledid', set an LED state to ON or
        OFF for each value in the 'states_of_off' array (True means
        ON, False means OFF). This function only works on LEDs 0 to
        99, and excludes the botton two special button rows.

        If 'start_ledid' plus the length of 'states_on_off' exceed the
        max LED ID (99), the operation continues, but wraps back
        around to led 0.

        There is a maximum of 100 LED states that can be written at a
        time.

        Args:
            start_ledid (int): ID of first LED in the range.
            code (:obj:`list` of :obj:`bool`): List of states to
                set. Max length 100

        """

        if start_ledid > 99 or start_ledid < 0:
            raise ValueError("start_ledid must be between 0 and 99; not %d" % start_ledid)

        num_leds = len(states_on_off)
        if num_leds == 0:
            return
        if num_leds > 100:
            raise ValueError("Only up to 100 leds may be set at a time, not %d" % num_leds)

        if num_leds == 71:
            num_leds_2 = 1
        elif num_leds > 77:
            num_leds_2 = num_leds - 77
        else:
            num_leds_2 = 0

        num_leds = num_leds - num_leds_2
        self._set_led_range_state_raw(start_ledid, states_on_off[:num_leds])
        if num_leds_2:
            self._set_led_range_state_raw((start_ledid + num_leds) % 100,
                                          states_on_off[num_leds:])

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

        ret = self._tx(b'\x85' + bytes([0x20 | state, ATT26A._shift7_left(ledID)]))
        if ret:
            raise IncorrectResponseError("set_led_state expects no return data, got %s" % ret)

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

    def get_led_status(self, ledID):
        """Set the state of an individual led on the bottom two rows.

        This function is not terribly useful. It is recommended that
        you keep track of the state of the 26A's LEDs yourself.

        Args:
            ledID (int): ID of the LED to get the state of.
                Range: 100 <= 'ledID' <= 119
        """

        if 100 > ledID or ledID >= 120:
            raise ValueError("ledID must be 100 <= ledID < 120; not %d" % ledID)

        ret = self._tx(b'\xA5\x20' + bytes([ATT26A._shift7_left(ledID)]))

        if (ret[0] & 0x08):
            ret_id = (ret[1] & 0x1F) + 100
        else:
            ret_id = (ret[0] & 0x07) + 100

        if ret_id != ledID:
            raise IncorrectResponseError("Wrong ID; Got %d, expected %d." % (ret_id, ledID))

        return LED_MODES[(ret[0] >> 4) & 3]

    @property
    def is_open(self):
        return self.__is_open

    @staticmethod
    def _shift7_left(b):
        return ((b << 1) & 0x7E) | ((b & 0x40) >> 6)

    @staticmethod
    def _shift7_right(b):
        return ((b & 0x7E) >> 1) | ((b & 0x01) << 6)

    @staticmethod
    def openSerialPortByName(devname):
        try:
            ser = serial.serial_for_url(
                devname, baudrate=10752, bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_ODD, stopbits=serial.STOPBITS_ONE)

            from serial.rfc2217 import Serial as rfc2217Serial
            if isinstance(ser, rfc2217Serial):
                print("WARNING: As of pyserial 3.4, rfc2217 adapters do not support write "
                      "timeouts. This can cause stalling in some error cases.")
            else:
                ser.write_timeout=0.1

            return ser
        except serial.serialutil.SerialException as e:
            raise CanNotOpenDeviceError("The 'devname' provided could not be opened: '%s'"%devname)
