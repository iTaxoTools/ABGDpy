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


class Header(QtWidgets.QWidget):
    """

    """
    def __init__(self):
        """
        """
        super().__init__()

        self._title = None
        self._logoTool = None
        self._logoProject = None

        self.logoSize = 86

        self.draw()

    def draw(self):
        """
        """
        self.setStyleSheet('background: red;')

        self.labelLogoTool = QtWidgets.QLabel()
        self.labelTitle = QtWidgets.QLabel('TITLE')
        font = self.labelTitle.font()
        font.setBold(True)
        font.setPointSize(22);
        self.labelTitle.setFont(font)
        self.labelDescription = QtWidgets.QLabel('DESCRIPTION')
        self.labelCitation = QtWidgets.QLabel('CITATION')
        self.labelLogoProject = QtWidgets.QLabel()

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.labelTitle, 0, 0)
        grid.addWidget(self.labelDescription, 0, 1)
        grid.addWidget(self.labelCitation, 1, 0, 1, 2)
        grid.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.labelLogoTool)
        layout.addLayout(grid)
        layout.addWidget(self.labelLogoProject)
        layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(layout)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.labelTitle.setText(title)
        self._title = title

    @property
    def logoTool(self):
        return self._logoTool

    @title.setter
    def logoTool(self, logo):
        self.labelLogoTool.setPixmap(
            logo.scaled(self.logoSize,self.logoSize))
        self._logoTool = logo

    @property
    def logoProject(self):
        return self._logoProject

    @title.setter
    def logoProject(self, logo):
        self.labelLogoProject.setPixmap(
            logo.scaled(self.logoSize,self.logoSize))
        self._logoProject = logo


class Pane(QtWidgets.QWidget):
    """

    """
    def __init__(self):
        """
        """
        super().__init__()
        self._title = None

        self.setStyleSheet('background: green;')

        self.labelTitle = QtWidgets.QLabel('TITLE GO HERE')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.labelTitle)
        layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(layout)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.labelTitle.setText(title)
        self._title = title


class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        logging.getLogger().setLevel(logging.DEBUG)
        self.analysis = None

        self.setWindowTitle("ABGDpy")
        self.setWindowIcon(QtGui.QIcon(':/icons/pyr8s-icon.png'))
        self.resize(854,480)

        self.machine = None
        self.act()
        self.draw()
        # self.stateInit()

        # if init is not None:
        #     self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def act(self):
        """Populate dialog actions"""
        self.action = {}

        self.action['open'] = QtWidgets.QAction('&Open', self)
        self.action['open'].setShortcut('Ctrl+O')
        self.action['open'].setStatusTip('Open an existing file')
        self.action['open'].triggered.connect(lambda: print(42))

        self.action['save'] = QtWidgets.QAction('&Save', self)
        self.action['save'].setShortcut('Ctrl+S')
        self.action['save'].setStatusTip('Save selected file')
        self.action['save'].triggered.connect(lambda: print(24))

        for key in self.action.keys():
            self.addAction(self.action[key])

    def draw(self):
        """Draw all widgets"""
        self.header = Header()
        self.header.title = 'ABGDpy'
        self.header.logoTool = QtGui.QPixmap(':/icons/pyr8s-icon.png')
        self.header.logoProject = QtGui.QPixmap(':/icons/itaxotools-micrologo.png')

        self.pane = {}

        self.pane['param'] = Pane()
        self.pane['param'].title = 'param'

        self.pane['list'] = Pane()
        self.pane['list'].title = 'list'

        self.pane['preview'] = Pane()
        self.pane['preview'].title = 'preview'

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.pane['param'])
        self.splitter.addWidget(self.pane['list'])
        self.splitter.addWidget(self.pane['preview'])
        self.splitter.setStyleSheet("QSplitter::handle { height: 8px; }")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.splitter)
        self.splitter.setStretchFactor(0,1)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setStretchFactor(2,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setCollapsible(2,False)

        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        self.setContentsMargins(5,5,5,5)

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
