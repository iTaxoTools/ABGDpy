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

class SquareImage(QtWidgets.QLabel):
    """Width will always equal height"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = None

    def minimumSizeHint(self):
        if self._size is not None:
            return QtCore.QSize(self._size, self._size)
        else:
            return super().minimumSizeHint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._size = max(event.size().height(), event.size().width())
        self.updateGeometry()
        print(self,event.size())


class Header(QtWidgets.QFrame):
    """
    The Taxotools toolbar, with space for a title, description,
    citations and two logos.
    """
    def __init__(self):
        """ """
        super().__init__()

        self._title = None
        self._description = None
        self._citation = None
        self._logoTool = None
        self._logoProject = None

        self.logoSize = 64

        self.draw()

    def draw(self):
        """ """
        self.setContentsMargins(5,5,5,5)
        self.setStyleSheet("""
            Header {
                background: transparent;
                border-bottom: 2px solid palette(Dark);
                }
            """)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        self.labelTitle = QtWidgets.QLabel('TITLE')
        self.labelTitle.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #595b61")

        self.labelDescription = QtWidgets.QLabel('DESCRIPTION')
        self.labelDescription.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #595b61")

        self.labelCitation = QtWidgets.QLabel('CITATION')
        self.labelCitation.setStyleSheet(
            "font-size: 11px;")

        self.labelLogoTool = SquareImage()
        self.labelLogoTool.setAlignment(QtCore.Qt.AlignCenter)

        self.labelLogoProject = SquareImage()
        self.labelLogoProject.setAlignment(QtCore.Qt.AlignCenter)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(38,38))
        self.toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.toolbar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        self.toolbar.actionTriggered.connect(lambda x: print(x))

        left = QtWidgets.QGridLayout()
        left.addWidget(self.labelLogoTool, 0, 0, 2, 1)
        left.addWidget(self.labelTitle, 0, 1)
        left.addWidget(self.labelDescription, 0, 2)
        left.addWidget(self.labelCitation, 1, 1, 1, 2)
        left.setColumnStretch(0,0)
        left.setColumnStretch(1,0)
        left.setColumnStretch(2,1)
        left.setContentsMargins(0, 0, 0, 0)
        left.setHorizontalSpacing(12)
        left.setVerticalSpacing(0)

        right = QtWidgets.QHBoxLayout()
        right.addWidget(self.toolbar, 0)
        right.addStretch(1)
        right.addWidget(self.labelLogoProject, 0)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(12)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(left, 5)
        layout.addLayout(right, 3)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.labelTitle.setText(title)
        self._title = title

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self.labelDescription.setText(description)
        self._description = description

    @property
    def citation(self):
        return self._citation

    @citation.setter
    def citation(self, citation):
        self.labelCitation.setText(citation)
        self._citation = citation

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
    def __init__(self, parent):
        """
        """
        super().__init__(parent=parent)
        self._title = None
        self._foot = None

        if not hasattr(parent, '_pane_foot_height'):
            parent._pane_foot_height = None
        self.draw()

    def draw(self):
        """ """
        # self.setStyleSheet('background: green;')

        self.labelTitle = QtWidgets.QLabel('TITLE GO HERE')
        self.labelTitle.setIndent(4)
        self.labelTitle.setMargin(2)
        self.labelTitle.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.labelTitle.setStyleSheet("""
            QLabel {
                indent: 32px;
                font-size: 14px;
                font-weight: bold;
                color: #595b61;
                background: transparent;
                border-bottom: 1px solid palette(Dark);
                }
            """)

        self.body = QtWidgets.QVBoxLayout()

        self.labelFoot = QtWidgets.QLabel('FOOTER')
        self.labelFoot.setAlignment(QtCore.Qt.AlignCenter)

        layoutFlags = QtWidgets.QHBoxLayout()
        layoutFlags.addWidget(self.labelFoot)
        layoutFlags.setContentsMargins(0, 0, 0, 0)
        self.foot = QtWidgets.QGroupBox()
        self.foot.setLayout(layoutFlags)
        self.foot.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.labelTitle, 0)
        layout.addLayout(self.body, 1)
        layout.addWidget(self.foot, 0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.labelTitle.setText(title)
        self._title = title

    @property
    def footer(self):
        return self._foot

    @title.setter
    def footer(self, footer):
        self.labelFoot.setText(footer)
        self._foot = footer


class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        logging.getLogger().setLevel(logging.DEBUG)
        self.analysis = core.BarcodeAnalysis(None)

        self.setWindowTitle("ABGDpy")
        self.setWindowIcon(QtGui.QIcon(':/icons/pyr8s-icon.png'))
        self.resize(854,480)

        self.machine = None
        self.draw()
        self.act()
        self.cog()

        # self.stateInit()

        # if init is not None:
        #     self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def draw(self):
        """Draw all widgets"""
        self.header = Header()
        self.header.title = 'ABGDpy'
        self.header.logoTool = QtGui.QPixmap(':/icons/pyr8s-icon.png')
        self.header.logoProject = QtGui.QPixmap(':/icons/itaxotools-micrologo.png')
        self.header.description = (
            'Primary species delimitation' + '\n'
            'using automatic barcode gap discovery'
            )
        self.header.citation = (
            'ABGD by G Achaz, BIONJ by Olivier Gascuel' + '\n'
            'Python wrapper by S. Patmanidis'
        )

        self.pane = {}


        self.paramWidget = param_qt.ParamContainer(self.analysis.param, doc=False)
        # self.paramWidget.setStyleSheet("background: blue;")
        self.paramWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)

        self.pane['param'] = Pane(self)
        self.pane['param'].title = 'Parameters'
        self.pane['param'].footer = 'Hover for tips'
        self.pane['param'].body.addWidget(self.paramWidget)
        self.pane['param'].body.addStretch(1)

        self.pane['list'] = Pane(self)
        self.pane['list'].title = 'Files'
        self.pane['list'].body.addStretch(1)

        self.pane['preview'] = Pane(self)
        self.pane['preview'].title = 'Preview'
        self.pane['preview'].body.addStretch(1)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.pane['param'])
        self.splitter.addWidget(self.pane['list'])
        self.splitter.addWidget(self.pane['preview'])
        self.splitter.setStretchFactor(0,1)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setStretchFactor(2,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setCollapsible(2,False)
        self.splitter.setStyleSheet("QSplitter::handle { height: 12px; }")
        self.splitter.setContentsMargins(4, 4, 4, 4)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.splitter)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setContentsMargins(5,5,5,5)

    def act(self):
        """Populate dialog actions"""
        self.action = {}

        def iconFromPixmap(path):
            pixmap = QtGui.QPixmap(path)
            mask = pixmap.createMaskFromColor(
                QtGui.QColor('black'), QtCore.Qt.MaskOutColor)
            pixmap.fill(QtGui.QColor('#595b61'))
            pixmap.setMask(mask)
            return QtGui.QIcon(pixmap.scaled(32,32,transformMode=QtCore.Qt.SmoothTransformation))

        self.action['open'] = QtWidgets.QAction('&Open', self)
        self.action['open'].setIcon(iconFromPixmap(':/icons/folder-open-solid.svg'))
        self.action['open'].setShortcut(QtGui.QKeySequence.Open)
        self.action['open'].setStatusTip('Open an existing file')
        self.action['open'].triggered.connect(lambda: print(42))

        self.action['save'] = QtWidgets.QAction('&Save', self)
        self.action['save'].setIcon(iconFromPixmap(':/icons/save-solid.svg'))
        self.action['save'].setShortcut(QtGui.QKeySequence.Save)
        self.action['save'].setStatusTip('Save selected file')
        self.action['save'].triggered.connect(lambda: print(24))

        self.action['run'] = QtWidgets.QAction('&Run', self)
        self.action['run'].setIcon(iconFromPixmap(':/icons/play-circle-regular.svg'))
        self.action['run'].setShortcut('Ctrl+R')
        self.action['run'].setStatusTip('Run analysis')
        self.action['run'].triggered.connect(lambda: print(24))

        self.action['stop'] = QtWidgets.QAction('Stop', self)
        self.action['stop'].setIcon(iconFromPixmap(':/icons/stop-circle-regular.svg'))
        self.action['stop'].setShortcut(QtGui.QKeySequence.Cancel)
        self.action['stop'].setStatusTip('Cancel analysis')
        self.action['stop'].triggered.connect(lambda: print(24))

        for action in self.action.values():
            self.header.toolbar.addAction(action)

    def cog(self):
        """Define state machine"""
        self.state = {}
        self.state['idle'] = QtCore.QState()
        self.state['idle_none'] = QtCore.QState(self.state['idle'])
        self.state['idle_open'] = QtCore.QState(self.state['idle'])
        self.state['idle_done'] = QtCore.QState(self.state['idle'])
        self.state['idle_last'] = QtCore.QHistoryState(self.state['idle'])
        self.state['idle'].setInitialState(self.state['idle_none'])
        self.state['running'] = QtCore.QState()

        self.machine = QtCore.QStateMachine(self)
        self.machine.addState(self.state['idle'])
        self.machine.addState(self.state['running'])
        self.machine.setInitialState(self.state['idle'])
        self.machine.start()

        self.state['idle'].assignProperty(self.action['stop'], 'visible', False)

        self.state['idle_none'].assignProperty(self.action['run'], 'enabled', False)
        self.state['idle_none'].assignProperty(self.action['save'], 'enabled', False)

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
