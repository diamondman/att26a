#! /usr/bin/env python3
import att26a
from att26a.simulator import Att26aSimBase

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui

import logging

# Parse the ui file once.
import sys, os.path
from PyQt5 import uic
thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir) # Needed to load ui
Att26aSimUi, Att26aSimUiBase = uic.loadUiType(os.path.join(thisdir, 'main.ui'))
del sys.path[-1] # Remove the now unnecessary path entry

__title__ = 'att26aguisim'
__version__ = '0.0.1'
__author__ = 'Jessy Diamond Exum'

palette_blink1 = QtGui.QPalette()
palette_blink1.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.blue))

palette_blink2 = QtGui.QPalette()
palette_blink2.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.green))

palette_off_on = QtGui.QPalette()
palette_off_on.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.red))

class Att26ASimQt(QtWidgets.QMainWindow):
    signal_set_led_state = QtCore.pyqtSignal(int, int)
    signal_set_led_range_state = QtCore.pyqtSignal(int, list)
    class Att26aSimInstrumentor(Att26aSimBase):
        def __init__(self, serialdev, qtsim):
            super().__init__(serialdev)
            self.qtsim = qtsim

        def on_set_led_range_state(self, start_ledid, states_on_off):
            self.qtsim.signal_set_led_range_state.emit(start_ledid, states_on_off)

        def on_set_led_state(self, state, ledID):
            self.qtsim.signal_set_led_state.emit(state, ledID)

        def on_set_factory_test_mode_enable(self, enable):
            self.qtsim.on_set_factory_test_mode_enable(enable)

        def on_set_IO_enable(self, enable):
            self.qtsim.on_set_IO_enable(enable)

        def on_get_led_status(self, ledID):
            return self.on_get_led_status(ledID)

    def on_set_led_range_state(self, start_ledid, states_on_off):
        self._log.info("Setting %d LEDs starting at %d"%(len(states_on_off), start_ledid))
        for i, state in enumerate(states_on_off):
            led = self.leds[(start_ledid + i) % 100]
            led.setPalette(palette_off_on)
            led.setValue(state)

    def on_set_led_state(self, state, ledID):
        self._log.info("Setting led %d's state to %d IN PASS THROUGH"%(ledID, state))
        led = self.leds[ledID]
        ison = True
        if state == att26a.LED_ON:
            led.setPalette(palette_off_on)
        elif state == att26a.LED_BLINK1:
            led.setPalette(palette_blink1)
        elif state == att26a.LED_BLINK2:
            led.setPalette(palette_blink2)
        else:
            led.setPalette(palette_off_on)
            ison = False

        led.setValue(ison)

    def on_set_factory_test_mode_enable(self, enable):
        self._log.info("%s factory test" % "Enable" if enable else "Disable")
        self._factory_test = enable

    def on_set_IO_enable(self, enable):
        self._log.info("%s IO driver" % "Enable" if enable else "Disable")
        self._io_enabled = enable

    def on_get_led_status(self, ledID):
        self._log.info("Reading led %d state" % ledID)
        return self.leds[ledID].value()

    def __init__(self, serialdev, log=None):
        super(Att26ASimQt, self).__init__()
        self.ui = Att26aSimUi()
        self.ui.setupUi(self)

        # Set the signals for button presses
        for btn_num in range(120):
            btn = self.findChild(QtWidgets.QPushButton, "btn_%03d"%btn_num)
            btn.pressed.connect(self.on_any_btn_press)

        self.leds = [self.findChild(QtWidgets.QProgressBar, "led_%03d"%btn_num)
                     for btn_num in range(120)]
        self._factory_test = False
        self._io_enabled = True

        self.signal_set_led_state.connect(self.on_set_led_state)
        self.signal_set_led_range_state.connect(self.on_set_led_range_state)

        self.__sim = Att26ASimQt.Att26aSimInstrumentor(serialdev, self)

        self._log = logging.getLogger('att26aguisim') if not log else log

    @QtCore.pyqtSlot()
    def on_any_btn_press(self):
        btn_num = int(self.sender().text())
        self.__sim.send_btn_press(btn_num)


def run(app, serialdev):
    window = Att26ASimQt(serialdev)
    window.show()

    return app.exec_() # Start the event loop.

def main_bootstrap(serialdev):
    import sys

    # Initialize the QApplication object, and free it last.
    # Not having this in a different function than other QT
    # objects can cause segmentation faults as app is freed
    # before the QWidgets.
    app = QtWidgets.QApplication(sys.argv)

    # Allow Ctrl-C to interrupt QT by scheduling GIL unlocks.
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None) # Let the interpreter run.

    sys.exit(run(app, serialdev))

def main_api(address="", port=7778, log=None):
    from att26a.serial_adapter import RFC2217SerialAdapter
    r = RFC2217SerialAdapter(address, port, log)
    main_bootstrap(r)

def main_cli():
    import argparse
    from att26a.clihelper import VAction

    parser = argparse.ArgumentParser(description='AT&T 26A graphical simulator')
    parser.add_argument('--port', type=int, nargs='?', default=7778,
                        help='Port to host rfc2217 server.')
    parser.add_argument('--addr', type=str, default="localhost",
                        help='Address to host rfc2217 server.')
    parser.add_argument('-v', nargs='?', action=VAction, dest='verbose', default=0,
                        help="Provide debug information. More than one v supported")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO) # Enable root filter to see serial logs
    logging.getLogger('RFC2217SerialAdapter').setLevel(logging.INFO)

    if args.verbose >= 2:
        loglevel = logging.DEBUG
        logging.basicConfig(level=loglevel)
    elif args.verbose >= 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING

    logging.getLogger('att26aguisim').setLevel(loglevel)

    main_api(args.addr, args.port)

def _main_subprocess_bootstrap(q):
    q.put(23)
    main_api(port=0)

def start_subprocess():
    import multiprocessing as mp
    mp.set_start_method("spawn")
    q = mp.Queue()
    p = mp.Process(target=_main_subprocess_bootstrap, args=(q,))
    p.start()
    return q.get()

if __name__ == "__main__":
    main_cli()
