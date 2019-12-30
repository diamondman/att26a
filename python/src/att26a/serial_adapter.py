#!/usr/bin/env python3

import logging
import socket
import sys
import time
import threading
import serial
import serial.rfc2217
import queue

from att26a import interruptablequeue

class RFC2217SerialAdapter(object):
    class FakePort(object):
        def __init__(self, realport):
            self.realport = realport

        @property
        def cts(self):
            return self.realport._cts
        @cts.setter
        def cts(self, value):
            self.realport._cts = value

        @property
        def dsr(self):
            return self.realport._dsr
        @dsr.setter
        def dsr(self, value):
            self.realport._dsr = value

        @property
        def ri(self):
            return self.realport._ri
        @ri.setter
        def ri(self, value):
            self.realport._ri = value

        @property
        def cd(self):
            return self.realport._cd
        @cd.setter
        def cd(self, value):
            self.realport._cd = value

        @property
        def baudrate(self):
            return self.realport._baudrate
        @baudrate.setter
        def baudrate(self, value):
            self.realport._baudrate = value

        @property
        def bytesize(self):
            return self.realport._bytesize
        @bytesize.setter
        def bytesize(self, value):
            self.realport._bytesize = value

        @property
        def parity(self):
            return self.realport._parity
        @parity.setter
        def parity(self, value):
            self.realport._parity = value

        @property
        def stopbits(self):
            return self.realport._stopbits
        @stopbits.setter
        def stopbits(self, value):
            self.realport._stopbits = value

        @property
        def xonxoff(self):
            return self.realport._xonxoff
        @xonxoff.setter
        def xonxoff(self, value):
            self.realport._xonxoff = value

        @property
        def rtscts(self):
            return self.realport._rtscts
        @rtscts.setter
        def rtscts(self, value):
            self.realport._rtscts = value

        @property
        def break_condition(self):
            return self.realport._break_condition
        @break_condition.setter
        def break_condition(self, value):
            self.realport._break_condition = value

        @property
        def dtr(self):
            return self.realport._dtr
        @dtr.setter
        def dtr(self, value):
            self.realport._dtr = value

        @property
        def rts(self):
            return self.realport._rts
        @rts.setter
        def rts(self, value):
            self.realport._rts = value

        def reset_input_buffer(self):
            pass
        def reset_output_buffer(self):
            pass

    class FakeConnection(object):
        def __init__(self, realconn):
            self.realconn = realconn

        def write(self, data):
            """thread safe socket write with no data escaping. used to send telnet stuff"""
            with self.realconn._write_lock:
                if self.realconn.socket:
                    self.realconn.socket.sendall(data)

    def __init__(self, address="", port=7778, log=None):
        self._address = address
        self._port = port
        self._is_open = False

        self._cts = False
        self._dsr = False
        self._ri = False
        self._cd = False
        self._baudrate = False
        self._bytesize = False
        self._parity = False
        self._stopbits = False
        self._xonxoff = False
        self._rtscts = False
        self._break_condition = False
        self._dtr = False
        self._rts = False

        self.connection_alive = False
        self.socket = None
        self._write_lock = threading.Lock()
        self.rfc2217 = None
        self.__reader = interruptablequeue.InterruptableQueue()

        self._log = logging.getLogger('RFC2217SerialAdapter') if not log else log

        self.thread_server = None

        self.open()

    def open(self):
        if not self._is_open:
            self._is_open = True
            self.thread_server = threading.Thread(
                target=self.server_thread, daemon=True
            )
            self.thread_server.start()

    def close(self):
        if self._is_open:
            self._is_open = False

            if self.socket: # Break out of socket recv()
                self.socket.shutdown(socket.SHUT_RDWR)
            else:           # Break out of server accept()
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self._address, self._port))

            # Sync up threads
            self.thread_server.join()

    def server_thread(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self._address, self._port))
        srv.listen(1)
        self._log.info("TCP/IP port: {}".format(self._port))

        while self._is_open:
            try:
                self.socket, addr = srv.accept()
                if not self._is_open:
                    self._log.debug("breaking out of accept")
                    break
                self._log.info('Connected by {}:{}'.format(addr[0], addr[1]))
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.rfc2217 = serial.rfc2217.PortManager(
                    RFC2217SerialAdapter.FakePort(self),
                    RFC2217SerialAdapter.FakeConnection(self),
                    logger=logging.getLogger('rfc2217.server')
                )
                self.connection_alive = True

                try:
                    while self.connection_alive:
                        try:
                            data = self.socket.recv(1024)
                            if not data:
                                self._log.debug("Breaking out of recv")
                                break
                            data_in = b''.join(self.rfc2217.filter(data))
                            for b in data_in:
                                self.__reader.put(b)
                        except socket.error as msg:
                            self._log.error('{}'.format(msg))
                            break
                finally:
                    self._log.info('Disconnected')
                    self.connection_alive = True
                    self.socket.close()
                    self.socket = None
            except socket.error as msg:
                self._log.error(str(msg))

        self._log.debug("server_thread dead")

    def write(self, data):
        if not self._is_open: raise Exception("Closed")
        with self._write_lock:
            if self.socket:
                # escape outgoing data when needed (Telnet IAC (0xff) character)
                self.socket.sendall(b''.join(self.rfc2217.escape(data)))

    def read(self, length):
        if not self._is_open: raise Exception("Closed")
        if length != 1:
            raise ValueError("multi byte read does not work yet")
        while True:
            try:
                return bytes([self.__reader.get(block=True, timeout=0.3)])
            except queue.Empty as e:
                if not self._is_open:
                    raise Exception("Closed")

    @property
    def cts(self):
        return self._cts
    @cts.setter
    def cts(self, value):
        self._cts = value
        self.rfc2217.check_modem_lines()

    @property
    def dsr(self):
        return self._dsr
    @dsr.setter
    def dsr(self, value):
        self._dsr = value
        self.rfc2217.check_modem_lines()

    @property
    def ri(self):
        return self._ri
    @ri.setter
    def ri(self, value):
        self._ri = value
        self.rfc2217.check_modem_lines()

    @property
    def cd(self):
        return self._cd
    @cd.setter
    def cd(self, value):
        self._cd = value
        self.rfc2217.check_modem_lines()

    @property
    def baudrate(self):
        return self._baudrate
    @baudrate.setter
    def baudrate(self, value):
        self._baudrate = value

    @property
    def bytesize(self):
        return self._bytesize

    @property
    def parity(self):
        return self._parity

    @property
    def stopbits(self):
        return self._stopbits

    @property
    def xonxoff(self):
        return self._xonxoff

    @property
    def rtscts(self):
        return self._rtscts

    @property
    def break_condition(self):
        return self._break_condition

    @property
    def dtr(self):
        return self._dtr

    @property
    def rts(self):
        return self._rts

    def reset_input_buffer(self):
        pass
    def reset_output_buffer(self):
        pass
