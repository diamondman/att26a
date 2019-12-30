import collections
import threading
import math
import time
import logging

LED_OFF = 0x0
LED_BLINK1 = 0x8
LED_BLINK2 = 0xD
LED_ON = 0xF

LED_MODES = (LED_OFF, LED_BLINK1, LED_BLINK2, LED_ON)

MSG_KA = 0xFF # Keep Alive
MSG_ACK = 0xFD # Acknowledge

class Att26aSimBase(object):
    def __init__(self, serialdev, log=None):
        self.__ser = serialdev
        self.__recvbuff = collections.deque(maxlen=16)

        self.__do_recvthread = False
        self.__recvthread = None

        self.__do_keepalivethread = False
        self.__keepalivethread = None

        self._log = logging.getLogger('att26asim') if not log else log

        self.reset()

    def reset(self):
        # Terminate the reader thread
        self.__do_recvthread = False
        if self.__recvthread is not None:
            self.__recvthread.wait(0.5)

        # (Re)start the reader thread
        self.__do_recvthread = True
        self.__recvthread = threading.Thread(daemon=True, target=self.__recvthread_func)
        self.__recvthread.start()

        # Terminate the writer thread
        self.__do_keepalivethread = False
        if self.__keepalivethread is not None:
            self.__keepalivethread.wait(0.5)

        # (Re)start the reader thread
        self.__do_keepalivethread = True
        self.__keepalivethread = threading.Thread(
            daemon=True, target=self.__keepalivethread_func)
        self.__keepalivethread.start()

    def __recvthread_func(self):
        retdata = bytearray()
        while self.__do_recvthread:
            try:
                data = self.__ser.read(1) # Blocks
            except serial.serialutil.SerialException as e:
                self._log.error("ATT26A closing due to exception on receiver thread: '%s'" % e)
                self._close(dojoin=False)

            self._rx(data)

    def __keepalivethread_func(self):
        self._log.info("Simulator Keepalive Message Thread STARTING")
        while self.__do_keepalivethread:
            self.__ser.write(b'\xFF')
            time.sleep(0.026)

        self._log.info("Simulator Keepalive Message Thread TERMINATING")

    @staticmethod
    def _shift7_left(b):
        return ((b << 1) & 0x7E) | ((b & 0x40) >> 6)

    @staticmethod
    def _shift7_right(b):
        return ((b & 0x7E) >> 1) | ((b & 0x01) << 6)

    @staticmethod
    def _check_msg(msg):
        h = 0x7F
        for b in msg[1:-1]:
            h ^= b
        return h == msg[-1]

    def send_btn_press(self, btn_id):
        self.__ser.write(bytes((Att26aSimBase._shift7_left(btn_id),)))

    def _rx(self, data):
        for b in data:
            self._rx_byte(b)

    def _rx_byte(self, b):
        if 0 > b > 255: raise ValueError("Invalid byte value")
        if b == 0xFF:
            if len(self.__recvbuff) >= 2:
                msg = b"".join(self.__recvbuff)
                if not Att26aSimBase._check_msg(msg):
                    self._log.warn("Message failed verification, DROP!")
                else:
                    self._msg_dispatch(msg[:-1])
        elif b == 0x85 or b == 0xA5:
            self.__recvbuff.clear()
            self.__recvbuff.append(b.to_bytes(1, 'little'))
        else:
            self.__recvbuff.append(b.to_bytes(1, 'little'))

    def _msg_dispatch(self, msg):
        self._log.debug("Message:", msg)
        if len(msg) < 3:
            self._tx_ack()
            return
        msgcat, msgtype, msgparam = msg[0], msg[1], msg[2:]

        if msgcat == 0x85: # WRITE
            self._log.debug("Command type is WRITE")
            if msgtype == 0x07: # Set LED range ON/OFF (0-99)
                self._log.debug("TRYING TO DO LED RANGE", msgparam, len(msgparam))
                if len(msgparam) >= 3:
                    self._log.debug("Still trying")
                    led_id = Att26aSimBase._shift7_right(msgparam[0])
                    led_count = msgparam[1]
                    led_data = msgparam[2:]
                    self._log.debug(led_id, led_count, led_data)
                    self._log.debug("CHECKING", 0 <= led_id <= 99,
                          (1 <= led_count <= 70 or 72 <= led_count <= 76),
                          math.ceil(led_count/7.00) == len(led_data))
                    if 0 <= led_id <= 99 and \
                       (1 <= led_count <= 70 or 72 <= led_count <= 76) and \
                       math.ceil(led_count/7.00) == len(led_data):
                        state_array = []
                        for d in led_data:
                            if d & 0x80:
                                self._log.debug("Invalid set led range data byte %x"%d)
                                break
                            for bit in range(6,-1,-1):
                                self._log.debug("LEDCOUNT", led_count)
                                if led_count == -1: break
                                led_count -= 1;
                                state_array.append(bool((d >> bit) & 1))
                        else:
                            self.on_set_led_range_state(led_id, state_array)
            elif (msgtype & 0xF0) == 0x20: # Set LED state (0-119)
                led_state = (msgtype & 0x0F)
                led_id = Att26aSimBase._shift7_right(msgparam[0])
                if led_state in LED_MODES and 0 <= led_id <= 119:
                    self.on_set_led_state(led_state, led_id)
            elif msgtype == 0x10 and \
                 msgparam[0] == 0x6F: # Enable factory test
                self.on_set_factory_test_mode_enable(True)
            elif msgtype == 0x30 and \
                msgparam[0] == 0x4F: # Disable factory test
                self.on_set_factory_test_mode_enable(False)
            elif msgtype == 0x40 and \
                msgparam[0] == 0x3F: # Enable IO driver
                self.on_set_IO_enable(True)
            elif msgtype == 0x50 and \
                msgparam[0] == 0x2F: # Disable IO driver
                self.on_set_IO_enable(False)
        elif msgcat == 0xA5: # READ
            if msgtype == 0x20: # Return state of LED (100-119)
                led_id = Att26aSimBase._shift7_right(msgparam[0])
                if 100 <= led_id <= 119:
                    led_state = self.on_get_led_status(led_id) & 0x03
                    need_2nd_byte = led_id > 107
                    self._log.debug("Need 2nd byte: %s"%\
                                    ("YES" if need_2nd_byte else "NO"))
                    self._log.debug("LED STATE:", led_state)
                    data_out = bytes(0x80 | (led_state << 4) | \
                                     (need_2nd_byte << 3) |\
                                     (0 if need_2nd_byte else ((led_id-100) & 0x07)))
                    if need_2nd_byte:
                        data_out += bytes(0x80 | ((led_id - 100) & 0x1F))

                    data_out += bytes((MSG_ACK,))

                    self.__ser.write(data_out)
                    return
            else:
                self._log.warn("UNKNOWN COMMAND CATEGORY")

        self._tx_ack()

    def _tx_ack(self):
        self.__ser.write(b'\xFD')


    def on_set_led_range_state(self, start_ledid, states_on_off):
        self._log.info("Setting led range starting at %d:" % start_ledid, states_on_off)

    def on_set_led_state(self, state, ledID):
        self._log.info("Setting led %d's state to %d"%(ledID, state))

    def on_set_factory_test_mode_enable(self, enable):
        self._log.info("%s factory test" % "Enable" if enable else "Disable")

    def on_set_IO_enable(self, enable):
        self._log.info("%s IO driver" % "Enable" if enable else "Disable")

    def on_get_led_status(self, ledID):
        self._log.info("Reading led %d state" % ledID)
        return False


class Att26aSim(Att26aSimBase):
    def __init__(self, serialdev):
        super().__init__(serialdev)

        self.__ledstates = [LED_MODES.index(LED_OFF)]*120
        self._factory_test = False
        self._io_enabled = True

    def on_set_led_range_state(self, start_ledid, states_on_off):
        self._log.info("Setting led range starting at %d: (%d)" % (start_ledid, len(states_on_off)), states_on_off)

    def on_set_led_state(self, state, ledID):
        self._log.info("Setting led %d's state to %d"%(ledID, state))
        self.__ledstates[ledID] = LED_MODES.index(state)

    def on_set_factory_test_mode_enable(self, enable):
        self._log.info("%s factory test" % "Enable" if enable else "Disable")
        self._factory_test = enable

    def on_set_IO_enable(self, enable):
        self._log.info("%s IO driver" % "Enable" if enable else "Disable")
        self._io_enabled = enable

    def on_get_led_status(self, ledID):
        self._log.info("Reading led %d state" % ledID)
        return self.__ledstates[ledID]

class Att26aSimEventTester(Att26aSimBase):
    def __init__(self, serialdev):
        super().__init__(serialdev)
        self._events = []

    def on_set_led_range_state(self, start_ledid, states_on_off):
        self._events.append(("set_led_range_state", start_ledid, states_on_off))

    def on_set_led_state(self, state, ledID):
        self._events.append(("set_led_state", state, ledID))

    def on_set_factory_test_mode_enable(self, enable):
        self._events.append(("set_factory_test_mode_enable", enable))

    def on_set_IO_enable(self, enable):
        self._events.append(("set_IO_enable", enable))

    def on_get_led_status(self, ledID):
        self._events.append(("get_led_status", enable))
        return False
