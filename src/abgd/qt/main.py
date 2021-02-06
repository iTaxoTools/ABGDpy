"""
GUI for ABGD ...
"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtSvg as QtSvg

import os
import sys
import logging
import tempfile
import time
import shutil
import pathlib
import re

from .. import core
from ..param import qt as param_qt

from . import utility
from . import icons

core.abgdc.separator = os.path.sep


class VPixmap(QtGui.QPixmap):
    """A colored vector pixmap"""
    def __init__(self, fileName, size=None, colormap=None):
        """
        Load an SVG resource file and replace colors according to
        provided dictionary `colormap`. Only fill and stroke is replaced.
        Also scales the pixmap if a QSize is provided.
        """
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QIODevice.ReadOnly):
            raise FileNotFoundError('Vector resource not found: ' + fileName)
        text = file.readAll().data().decode()
        file.close()

        if colormap is not None:
            # match options fill|stroke followed by a key color
            regex = '(?P<prefix>(fill|stroke)\:)(?P<color>' + \
                '|'.join(map(re.escape, colormap.keys()))+')'
            # replace just the color according to colormap
            text = re.sub(regex, lambda mo: mo.group('prefix') + colormap[mo.group('color')], text)

        renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(text.encode()))
        size = renderer.defaultSize() if size is None else size
        super().__init__(size)
        self.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self)
        renderer.render(painter)
        painter.end()

class VIcon(QtGui.QIcon):
    """A colored vector icon"""
    def __init__(self, fileName, colormap_modes):
        """Create pixmaps with colormaps matching the dictionary modes"""
        super().__init__()
        for mode in colormap_modes.keys():
            self.addPixmap(VPixmap(fileName,colormap=colormap_modes[mode]), mode)

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


class ResultItem(QtWidgets.QListWidgetItem):
    """
    Model for an ABGD analysis result file.
    Holds icon, label, tooltip, category and file location.
    """
    Type = QtWidgets.QListWidgetItem.UserType + 1
    Icons = { None: QtGui.QIcon() }

    def __init__(self, file, parent=None):
        """Overloaded with new type"""
        super().__init__(parent=parent, type=self.Type)
        self.file = file
        path = pathlib.Path(file)
        suffix = path.suffix
        if not (suffix in self.Icons.keys()):
            suffix = None
        self.setIcon(self.Icons[suffix])
        self.setText(path.name)

class ResultView(QtWidgets.QListWidget):
    """
    Show each result file with icon and label.
    Remember file type and path
    """
    def open(self, folder):
        """Refresh contents"""
        self.clear()
        path = pathlib.Path(folder)

        # graph files
        for file in sorted(list(path.glob('*.svg'))):
            ResultItem(str(path / file), self)

        # spart files
        for file in sorted(list(path.glob('*.spart'))):
            ResultItem(str(path / file), self)

        # partition files
        for file in sorted(list(path.glob('*.txt'))):
            ResultItem(str(path / file), self)

        # tree files
        for file in sorted(list(path.glob('*.tree'))):
            ResultItem(str(path / file), self)

        # log files
        for file in list(path.glob('*.log')):
            ResultItem(str(path / file), self)


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

        # self.toolbar.actionTriggered.connect(lambda x: print(x))

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
        self.labelLogoTool.setPixmap(logo)
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
        # self.labelTitle.setSizePolicy(
        #     QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Ignored)
        self.labelTitle.setStyleSheet("""
            QLabel {
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
        handler = logging.StreamHandler(sys.stdout)
        logging.getLogger().addHandler(handler)

        self.title = 'ABGDpy'
        self.analysis = core.BarcodeAnalysis(None)
        self._temp = None
        self.temp = None

        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon(':/icons/pyr8s-icon.png'))
        self.resize(854,480)

        self.machine = None
        self.skin()
        self.draw()
        self.act()
        self.cog()

        if init is not None:
            self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def skin(self):
        """Configure widget appearance"""
        self.colormap = {
            VIcon.Normal: {
                '#000000':  '#454241',
                '#ff0000':  '#ee4e5f',
                },
            VIcon.Disabled: {
                '#000000':  '#abaaa8',
                '#ff0000':  '#ffcccc',
                },
            }

        self.colormap_icon =  {
            '#000000':  '#655c5d',
            '#ff0000':  '#e2001a',
            '#ffa500':  '#eb6a4a',
            }
        ResultItem.Icons['.txt'] = \
            QtGui.QIcon(VPixmap(':/icons/file-text.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.svg'] = \
            QtGui.QIcon(VPixmap(':/icons/file-graph.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.log'] = \
            QtGui.QIcon(VPixmap(':/icons/file-log.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.spart'] = \
            QtGui.QIcon(VPixmap(':/icons/file-spart.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.tree'] = \
            QtGui.QIcon(VPixmap(':/icons/file-tree.svg',
                colormap=self.colormap_icon))

    def draw(self):
        """Draw all widgets"""
        self.header = Header()
        self.header.title = self.title
        self.header.logoTool = VPixmap(':/icons/abgd-logo.svg',
            colormap=self.colormap_icon)
        self.header.logoProject = QtGui.QPixmap(':/icons/itaxotools-micrologo.png')
        self.header.description = (
            'Primary species delimitation' + '\n'
            'using automatic barcode gap discovery'
            )
        self.header.citation = (
            'ABGD by G Achaz, S Brouillet, BIONJ by O Gascuel' + '\n'
            'Python wrapper by S Patmanidis'
        )

        self.line = QtWidgets.QFrame()
        self.line.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.line.setStyleSheet("""
            QFrame {
                background-color: #e1e0de;
                border-style: solid;
                border-width: 2px 0px 2px 0px;
                border-color: #abaaa8;
                }
            """)

        self.line.icon = QtWidgets.QLabel()
        self.line.icon.setPixmap(VPixmap(':/icons/arrow-right.svg',
            colormap=self.colormap_icon))
        self.line.icon.setStyleSheet('border-style: none;')

        self.line.file = QtWidgets.QLineEdit()
        self.line.file.setPlaceholderText('Open a file to start')
        self.line.file.setReadOnly(True)
        self.line.file.setStyleSheet("""
            background-color: white;
            padding: 2px 4px 2px 4px;
            """)

        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(4)
        layout.addWidget(self.line.icon)
        layout.addSpacing(2)
        layout.addWidget(self.line.file)
        layout.addSpacing(14)
        layout.setContentsMargins(4, 4, 4, 4)
        self.line.setLayout(layout)

        self.pane = {}

        self.paramWidget = param_qt.ParamContainer(self.analysis.param, doc=False)
        # self.paramWidget.setStyleSheet("background: blue;")
        self.paramWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)

        self.pane['param'] = Pane(self)
        self.pane['param'].title = 'Parameters'
        self.pane['param'].footer = 'Hover parameters for tips'
        self.pane['param'].body.addWidget(self.paramWidget)
        self.pane['param'].body.addStretch(1)

        self.folder = ResultView()
        self.folder.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.folder.itemActivated.connect(self.handlePreview)
        self.folder.setStyleSheet("ResultView::item {padding: 2px;}")

        self.pane['list'] = Pane(self)
        self.pane['list'].title = 'Files'
        self.pane['list'].footer = 'Nothing to show'
        self.pane['list'].body.addWidget(self.folder)
        self.pane['list'].body.setContentsMargins(5, 5, 5, 5)
        # self.pane['list'].body.addStretch(1)

        self.preview = QtWidgets.QTextEdit()
        self.preview.setFont(
            QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.preview.setReadOnly(True)

        self.graph = QtSvg.QSvgWidget()

        self.stack = QtWidgets.QStackedLayout()
        self.stack.addWidget(self.preview)
        self.stack.addWidget(self.graph)

        self.pane['preview'] = Pane(self)
        self.pane['preview'].title = 'Preview'
        self.pane['preview'].footer = 'Nothing to show'
        self.pane['preview'].body.addLayout(self.stack)
        self.pane['preview'].body.setContentsMargins(5, 5, 5, 5)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.pane['param'])
        self.splitter.addWidget(self.pane['list'])
        self.splitter.addWidget(self.pane['preview'])
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,0)
        self.splitter.setStretchFactor(2,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setCollapsible(2,False)
        self.splitter.setStyleSheet("QSplitter::handle { height: 12px; }")
        self.splitter.setContentsMargins(4, 4, 4, 4)
        self.splitter.setSizes([
            self.width()/4,
            self.width()/4,
            self.width()/2,
            ])

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.line)
        layout.addWidget(self.splitter)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setContentsMargins(5,5,5,5)

    def act(self):
        """Populate dialog actions"""
        self.action = {}

        self.action['open'] = QtWidgets.QAction('&Open', self)
        self.action['open'].setIcon(VIcon(':/icons/open.svg', self.colormap))
        self.action['open'].setShortcut(QtGui.QKeySequence.Open)
        self.action['open'].setToolTip((
            'Open an aligned fasta file or a distance matrix\n'
            'Accepted formats: phylip, dnadist and MEGA'))
        self.action['open'].triggered.connect(self.handleOpen)

        self.action['save'] = QtWidgets.QAction('&Save', self)
        self.action['save'].setIcon(VIcon(':/icons/save.svg', self.colormap))
        self.action['save'].setShortcut(QtGui.QKeySequence.Save)
        self.action['save'].setToolTip((
            'Save files with a prefix of your choice\n'
            'Change filter to choose what files are saved'))
        self.action['save'].triggered.connect(self.handleSave)

        self.action['run'] = QtWidgets.QAction('&Run', self)
        self.action['run'].setIcon(VIcon(':/icons/run.svg', self.colormap))
        self.action['run'].setShortcut('Ctrl+R')
        self.action['run'].setToolTip('Run ABGD analysis')
        self.action['run'].triggered.connect(self.handleRun)

        self.action['stop'] = QtWidgets.QAction('Stop', self)
        self.action['stop'].setIcon(VIcon(':/icons/stop.svg', self.colormap))
        self.action['stop'].setShortcut(QtGui.QKeySequence.Cancel)
        self.action['stop'].setToolTip('Cancel analysis')
        self.action['stop'].triggered.connect(self.handleStop)

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

        state = self.state['idle']
        state.assignProperty(self.action['run'], 'visible', True)
        state.assignProperty(self.action['stop'], 'visible', False)
        state.assignProperty(self.action['open'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', True)

        state = self.state['idle_none']
        state.assignProperty(self.action['run'], 'enabled', False)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', False)
        state.assignProperty(self.pane['param'].foot, 'enabled', False)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Nothing to show')
        state.assignProperty(self.pane['preview'], 'enabled', False)

        state = self.state['idle_open']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.pane['param'].foot, 'enabled', True)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Nothing to show')
        state.assignProperty(self.pane['preview'], 'enabled', False)

        state = self.state['idle_done']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', True)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.pane['param'].foot, 'enabled', True)
        state.assignProperty(self.pane['list'], 'enabled', True)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Double-click for preview')
        state.assignProperty(self.pane['preview'], 'enabled', True)

        state = self.state['running']
        state.assignProperty(self.action['run'], 'visible', False)
        state.assignProperty(self.action['stop'], 'visible', True)
        state.assignProperty(self.action['open'], 'enabled', False)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', False)
        state.assignProperty(self.pane['param'].foot, 'enabled', False)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['preview'], 'enabled', False)

        transition = utility.NamedTransition('OPEN')
        def onTransition(event):
            file = event.kwargs['file']
            fileInfo = QtCore.QFileInfo(file)
            fileName = fileInfo.fileName()
            absolute = fileInfo.absoluteFilePath()
            self.setWindowTitle(self.title + ' - ' + fileName)
            self.line.file.setText(file)
            self.analysis.file = absolute
            self.folder.clear()
            self.preview.clear()
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_open'])
        self.state['idle'].addTransition(transition)

        transition = utility.NamedTransition('RUN')
        transition.setTargetState(self.state['running'])
        self.state['idle'].addTransition(transition)

        transition = utility.NamedTransition('DONE')
        def onTransition(event):
            self.folder.open(self.temp.name + '/')
            self.folder.setCurrentItem(self.folder.item(0))
            self.handlePreview(self.folder.item(0))
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Analysis complete.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_done'])
        self.state['running'].addTransition(transition)

        transition = utility.NamedTransition('FAIL')
        def onTransition(event):
            self.folder.open(self._temp.name + '/')
            self.folder.setCurrentItem(self.folder.item(0))
            self.handlePreview(self.folder.item(0))
            self.fail(event.args[0])
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_done'])
        self.state['running'].addTransition(transition)

        transition = utility.NamedTransition('CANCEL')
        transition.setTargetState(self.state['idle_last'])
        self.state['running'].addTransition(transition)

        self.machine = QtCore.QStateMachine(self)
        self.machine.addState(self.state['idle'])
        self.machine.addState(self.state['running'])
        self.machine.setInitialState(self.state['idle'])
        self.machine.start()

    def fail(self, exception):
        # raise exception
        # self.closeMessages()
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('An exception occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
        logger = logging.getLogger()
        logger.error(str(exception))

    def handleOpen(self, e, fileName=None):
        """Called by toolbar action: open"""
        if fileName is None:
            (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self,
                self.title + ' - Open File',
                str(pathlib.Path.cwd()),
                'All Files (*)',
                options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if len(fileName) == 0:
            return
        core.BarcodeAnalysis(fileName)
        self.paramWidget.setParams(self.analysis.param)
        self.machine.postEvent(utility.NamedEvent('OPEN',file=fileName))

    def handleSave(self):
        """Called by toolbar action: save"""
        path = pathlib.Path(self.analysis.file)

        # Dialog name filters with their file-selecting functions
        def fromSelection():
            return [pathlib.Path(item.file) for item in self.folder.selectedItems()]

        def fromFilter(filter):
            def _fromFilter():
                return list(pathlib.Path(self.temp.name).glob(filter))
            return _fromFilter

        nameFiltersWithSelectors = {
            'All files (*)': fromFilter('*.*'),
            'Selected files (*)': fromSelection,
            'Spart files (*.spart)': fromFilter('*.spart'),
            'Partition files (*.txt)': fromFilter('*.txt'),
            'Vector Graphics (*.svg)': fromFilter('*.svg'),
            'Log files (*.log)': fromFilter('*.log'),
            }

        # Widget-based dialog, filters decide what files are saved
        dialog = QtWidgets.QFileDialog()
        dialog.selectFile(str(path.stem))
        dialog.setDirectory(str(path.parent))
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setOptions(
            QtWidgets.QFileDialog.DontResolveSymlinks |
            QtWidgets.QFileDialog.DontUseNativeDialog
            )
        dialog.setNameFilters(nameFiltersWithSelectors.keys())

        # Disable file selection
        class ProxyModel(QtCore.QIdentityProxyModel):
            def flags(self, index):
                flags = super().flags(index)
                if not self.sourceModel().isDir(index):
                    flags &= ~QtCore.Qt.ItemIsSelectable
                    flags &= ~QtCore.Qt.ItemIsEnabled
                return flags
        proxy = ProxyModel(dialog)
        dialog.setProxyModel(proxy)

        # All files will have this as prefix
        saveTo = ''
        if (dialog.exec()):
            saveTo = dialog.selectedFiles()[0]
            print('SAVING TO:',saveTo)
        if len(saveTo) == 0:
            return
        save = pathlib.Path(saveTo)

        # Select the files that will be copied
        filesFrom = nameFiltersWithSelectors[dialog.selectedNameFilter()]()

        filesMap = {
            file: save.with_name(save.name + '.' + file.name)
            for file in filesFrom
            }

        # Check existing files for possible overwrites
        existing = set(save.parent.glob('*'))
        overlap = existing & set(filesMap.values())

        if len(overlap) > 0:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Question)
            msgBox.setText('Some files already exist. Overwrite?')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
            confirm = msgBox.exec()
            if confirm == QtWidgets.QMessageBox.No:
                return

        # Finally copy the files
        for file in filesMap.keys():
            print(file, '->', filesMap[file])
            shutil.copyfile(file, filesMap[file])

    def handleRun(self):
        """Called by toolbar action: run"""
        try:
            self.paramWidget.applyParams()
            self._temp = tempfile.TemporaryDirectory(prefix='abgd_')
            self.analysis.target = self._temp.name
            # print('RUN', self.analysis.target)
        except Exception as exception:
            self.fail(exception)
            return

        def done(result):
            # print('DONE', result)
            self.temp = self._temp
            self.analysis.results = result
            self.machine.postEvent(utility.NamedEvent('DONE', True))

        def fail(exception):
            self.machine.postEvent(utility.NamedEvent('FAIL', exception))

        self.launcher = utility.UProcess(self.workRun)
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        # self.launcher.setLogger(logging.getLogger())
        self.launcher.start()
        self.machine.postEvent(utility.NamedEvent('RUN'))

    def workRun(self):
        """Runs on the UProcess, defined here for pickability"""
        # print('WORK', self.analysis.file)
        # print('WORK', self.analysis.target)
        self.analysis.useLogfile = True
        self.analysis.run()
        # time.sleep(3)
        return self.analysis.results

    def handleStop(self):
        """Called by cancel button"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Cancel ongoing analysis?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            self.launcher.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

    def handlePreview(self, item):
        """Called by file double-click"""
        try:
            path = pathlib.Path(item.file)
            self.pane['preview'].footer = path.name
            if path.suffix == '.svg':
                self.stack.setCurrentWidget(self.graph)
                self.graph.load(str(path))
                self.graph.renderer().setAspectRatioMode(QtCore.Qt.KeepAspectRatio)
            else:
                self.stack.setCurrentWidget(self.preview)
                self.preview.clear()
                with open(item.file) as input:
                    for line in input:
                        self.preview.insertPlainText(line)
                format = QtGui.QTextBlockFormat()
                # format.setLineHeight(200, QtGui.QTextBlockFormat.ProportionalHeight)
                # format.setNonBreakableLines(True)
                format.setTopMargin(10)
                cursor = self.preview.textCursor()
                cursor.select(QtGui.QTextCursor.Document);
                cursor.mergeBlockFormat(format);
                self.preview.moveCursor(QtGui.QTextCursor.Start)
        except Exception as exception:
            self.fail(exception)
            return

def show(sys):
    """Entry point"""
    def init():
        if len(sys.argv) >= 2:
            main.handleOpen(None, fileName=sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main(init=init)
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    sys.exit(app.exec_())
