#! /usr/bin/env python3
from att26a.simulator import Att26aSimBase

from PyQt5 import QtCore
from PyQt5 import QtWidgets

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

class Att26ASimQt(QtWidgets.QMainWindow):
    signal_set_led_state = QtCore.pyqtSignal(int, int)
    class Att26aSimInstrumentor(Att26aSimBase):
        def __init__(self, serialdev, qtsim):
            super().__init__(serialdev)
            self.qtsim = qtsim

        def on_set_led_range_state(self, start_ledid, states_on_off):
            self.qtsim.on_set_led_range_state(start_ledid, states_on_off)

        def on_set_led_state(self, state, ledID):
            self.qtsim.signal_set_led_state.emit(state, ledID)
            #self.qtsim.on_set_led_state(state, ledID)

        def on_set_factory_test_mode_enable(self, enable):
            self.qtsim.on_set_factory_test_mode_enable(enable)

        def on_set_IO_enable(self, enable):
            self.qtsim.on_set_IO_enable(enable)

        def on_get_led_status(self, ledID):
            return self.on_get_led_status(ledID)

    def on_set_led_range_state(self, start_ledid, states_on_off):
        print("DATA VALID LOOKING!")

    def on_set_led_state(self, state, ledID):
        print("Setting led %d's state to %d IN PASS THROUGH"%(ledID, state))
        #mode = LED_MODES.index(state)
        self.leds[ledID].setValue(bool(state))

    def on_set_factory_test_mode_enable(self, enable):
        print("%s factory test" % "Enable" if enable else "Disable")
        self._factory_test = enable

    def on_set_IO_enable(self, enable):
        print("%s IO driver" % "Enable" if enable else "Disable")
        self._io_enabled = enable

    def on_get_led_status(self, ledID):
        print("Reading led %d state" % ledID)
        return self.leds[ledID].value()

    def __init__(self, serialdev):
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

        self.__sim = Att26ASimQt.Att26aSimInstrumentor(serialdev, self)

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

def main():
    from att26a.serial_adapter import RFC2217SerialAdapter
    r = RFC2217SerialAdapter()
    main_bootstrap(r)

def _main_subprocess_bootstrap(q):
    q.put(23)
    main(None)

def start_subprocess():
    import multiprocessing as mp
    mp.set_start_method("spawn")
    q = mp.Queue()
    p = mp.Process(target=_main_subprocess_bootstrap, args=(q,))
    p.start()
    return q.get()

if __name__ == "__main__":
    main()
