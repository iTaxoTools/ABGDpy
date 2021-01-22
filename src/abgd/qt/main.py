"""
GUI for ABGD ...
"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import sys
import logging
import re
import pickle

from .. import core
from ..param import qt as param_qt

from . import utility
from . import icons

class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        logging.getLogger().setLevel(logging.DEBUG)
        # self.analysis = core.RateAnalysis()

        self.setWindowTitle("ABGDpy")
        self.resize(854,480)
        self.machine = None
        # self.draw()
        # self.stateInit()

        # if init is not None:
        #     self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state




def show(sys):
    """Entry point"""
    def init():
        if len(sys.argv) >= 2:
            main.handleOpenFile(sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main(init=init)
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    sys.exit(app.exec_())
