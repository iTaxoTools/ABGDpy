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
from . import widgets
from . import resources


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

class Main(widgets.ToolDialog):
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
        self.setWindowIcon(QtGui.QIcon(':/resources/abgd-icon-transparent.ico'))
        self.resize(1024,480)

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
        color = {
            'white':  '#ffffff',
            'light':  '#eff1ee',
            'beige':  '#e1e0de',
            'gray':   '#abaaa8',
            'iron':   '#8b8d8a',
            'black':  '#454241',
            'red':    '#ee4e5f',
            'pink':   '#eb9597',
            'orange': '#eb6a4a',
            'brown':  '#655c5d',
            'green':  '#00ff00',
            }
        # using green for debugging
        palette = QtGui.QGuiApplication.palette()
        scheme = {
            QtGui.QPalette.Active: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'black',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'brown',
                QtGui.QPalette.Text: 'black',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'black',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'red',
                QtGui.QPalette.HighlightedText: 'white',
                # These work on linux only?
                QtGui.QPalette.ToolTipBase: 'beige',
                QtGui.QPalette.ToolTipText: 'brown',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            QtGui.QPalette.Disabled: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'iron',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'green',
                QtGui.QPalette.Text: 'iron',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'gray',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'pink',
                QtGui.QPalette.HighlightedText: 'white',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.ToolTipBase: 'green',
                QtGui.QPalette.ToolTipText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            }
        scheme[QtGui.QPalette.Inactive] = scheme[QtGui.QPalette.Active]
        for group in scheme:
            for role in scheme[group]:
                palette.setColor(group, role,
                    QtGui.QColor(color[scheme[group][role]]))
        QtGui.QGuiApplication.setPalette(palette)

        self.colormap = {
            widgets.VectorIcon.Normal: {
                '#000000': color['black'],
                '#ff0000': color['red'],
                },
            widgets.VectorIcon.Disabled: {
                '#000000': color['gray'],
                '#ff0000': color['orange'],
                },
            }
        self.colormap_icon =  {
            '#000000': color['black'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_icon_light =  {
            '#000000': color['iron'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_graph =  {
            'abgd': {
                'black':   color['black'],
                '#D82424': color['red'],
                '#EBE448': color['gray'],
                },
            'disthist': {
                'black':   color['black'],
                '#EBE448': color['beige'],
                },
            'rank': {
                'black':   color['black'],
                '#D82424': color['red'],
                },
            }

        ResultItem.Icons['.txt'] = \
            QtGui.QIcon(widgets.VectorPixmap(':/resources/file-text.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.svg'] = \
            QtGui.QIcon(widgets.VectorPixmap(':/resources/file-graph.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.log'] = \
            QtGui.QIcon(widgets.VectorPixmap(':/resources/file-log.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.spart'] = \
            QtGui.QIcon(widgets.VectorPixmap(':/resources/file-spart.svg',
                colormap=self.colormap_icon))
        ResultItem.Icons['.tree'] = \
            QtGui.QIcon(widgets.VectorPixmap(':/resources/file-tree.svg',
                colormap=self.colormap_icon))

    def draw(self):
        """Draw all widgets"""
        self.header = widgets.Header()
        self.header.logoTool = widgets.VectorPixmap(':/resources/abgd-logo.svg',
            colormap=self.colormap_icon)
        self.header.logoProject = QtGui.QPixmap(':/resources/itaxotools-micrologo.png')
        self.header.description = (
            'Primary species delimitation' + '\n'
            'using automatic barcode gap discovery'
            )
        self.header.citation = (
            'ABGD by G. Achaz, S. Brouillet, BIONJ by O. Gascuel' + '\n'
            'Python wrapper by S. Patmanidis'
        )

        self.line = widgets.Subheader()

        self.line.icon = QtWidgets.QLabel()
        self.line.icon.setPixmap(widgets.VectorPixmap(':/resources/arrow-right.svg',
            colormap=self.colormap_icon_light))
        self.line.icon.setStyleSheet('border-style: none;')

        self.line.file = QtWidgets.QLineEdit()
        self.line.file.setPlaceholderText('Open a file to begin')
        self.line.file.setReadOnly(True)
        self.line.file.setStyleSheet("""
            QLineEdit {
                background-color: palette(Base);
                padding: 2px 4px 2px 4px;
                border-radius: 4px;
                border: 1px solid palette(Mid);
                }
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
        self.paramWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        self.paramWidget.setContentsMargins(0, 0, 0, 0)
        self.paramWidget.paramChanged.connect(
            lambda e: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        self.pane['param'] = widgets.Panel(self)
        self.pane['param'].title = 'Parameters'
        self.pane['param'].footer = 'Hover parameters for tips'
        self.pane['param'].body.addWidget(self.paramWidget)
        self.pane['param'].body.addStretch(1)
        self.pane['param'].body.setContentsMargins(0, 0, 0, 0)

        self.folder = ResultView()
        self.folder.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.folder.itemActivated.connect(self.handlePreview)
        self.folder.setStyleSheet("ResultView::item {padding: 2px;}")
        self.folder.setAlternatingRowColors(True)

        self.pane['list'] = widgets.Panel(self)
        self.pane['list'].title = 'Files'
        self.pane['list'].footer = 'Nothing to show'
        self.pane['list'].body.addWidget(self.folder)
        self.pane['list'].body.setContentsMargins(1, 1, 1, 1)
        # self.pane['list'].body.addStretch(1)

        self.preview = QtWidgets.QTextEdit()
        self.preview.setFont(
            QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.preview.setReadOnly(True)

        self.graphSvg = QtSvg.QSvgWidget()

        self.graph = QtWidgets.QFrame()
        self.graph.setStyleSheet("""
            QFrame {
                background-color: palette(Base);
                border: 1px solid palette(Mid);
                }
            """)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.graphSvg)
        self.graph.setLayout(layout)

        self.stack = QtWidgets.QStackedLayout()
        self.stack.addWidget(self.preview)
        self.stack.addWidget(self.graph)

        self.pane['preview'] = widgets.Panel(self)
        self.pane['preview'].title = 'Preview'
        self.pane['preview'].footer = 'Nothing to show'
        self.pane['preview'].body.addLayout(self.stack)
        self.pane['preview'].body.setContentsMargins(1, 1, 1, 1)

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
        self.splitter.setContentsMargins(8, 4, 8, 4)
        self.splitter.setSizes([
            self.width()/4,
            self.width()/4,
            self.width()/2,
            ])

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.line)
        layout.addSpacing(8)
        layout.addWidget(self.splitter)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setContentsMargins(0, 0, 0, 0)

    def act(self):
        """Populate dialog actions"""
        self.action = {}

        self.action['open'] = QtWidgets.QAction('&Open', self)
        self.action['open'].setIcon(widgets.VectorIcon(':/resources/open.svg', self.colormap))
        self.action['open'].setShortcut(QtGui.QKeySequence.Open)
        self.action['open'].setToolTip((
            'Open an aligned fasta file or a distance matrix\n'
            'Accepted formats: phylip, dnadist and MEGA'))
        self.action['open'].triggered.connect(self.handleOpen)

        self.action['save'] = QtWidgets.QAction('&Save', self)
        self.action['save'].setIcon(widgets.VectorIcon(':/resources/save.svg', self.colormap))
        self.action['save'].setShortcut(QtGui.QKeySequence.Save)
        self.action['save'].setToolTip((
            'Save files with a prefix of your choice\n'
            'Change filter to choose what files are saved'))
        self.action['save'].triggered.connect(self.handleSave)

        self.action['run'] = QtWidgets.QAction('&Run', self)
        self.action['run'].setIcon(widgets.VectorIcon(':/resources/run.svg', self.colormap))
        self.action['run'].setShortcut('Ctrl+R')
        self.action['run'].setToolTip('Run ABGD analysis')
        self.action['run'].triggered.connect(self.handleRun)

        self.action['stop'] = QtWidgets.QAction('Stop', self)
        self.action['stop'].setIcon(widgets.VectorIcon(':/resources/stop.svg', self.colormap))
        # self.action['stop'].setShortcut(QtGui.QKeySequence.Cancel)
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
        self.state['idle_updated'] = QtCore.QState(self.state['idle'])
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
        state.assignProperty(self.pane['param'], 'enabled', False)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Nothing to show')
        state.assignProperty(self.pane['preview'], 'enabled', False)

        state = self.state['idle_open']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.pane['param'], 'enabled', True)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Nothing to show')
        state.assignProperty(self.pane['preview'], 'enabled', False)

        state = self.state['idle_done']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', True)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.pane['param'], 'enabled', True)
        state.assignProperty(self.pane['list'], 'enabled', True)
        state.assignProperty(self.pane['list'].labelFoot, 'text', 'Double-click for preview')
        state.assignProperty(self.pane['preview'], 'enabled', True)
        def onEntry(event):
            self.splitter.setSizes([1, 1, -1])
        state.onEntry = onEntry

        state = self.state['running']
        state.assignProperty(self.action['run'], 'visible', False)
        state.assignProperty(self.action['stop'], 'visible', True)
        state.assignProperty(self.action['open'], 'enabled', False)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', False)
        state.assignProperty(self.pane['param'], 'enabled', False)
        state.assignProperty(self.pane['list'], 'enabled', False)
        state.assignProperty(self.pane['preview'], 'enabled', False)

        state = self.state['idle_updated']
        def onEntry(event):
            tip = ( 'Parameters have changed,\n' +
                    're-run analysis to update results.')
            self.pane['param'].flag = '*'
            self.pane['list'].flag = '*'
            self.pane['preview'].flag = '*'
            self.pane['param'].flagTip = tip
            self.pane['list'].flagTip = tip
            self.pane['preview'].flagTip = tip
        state.onEntry = onEntry
        def onExit(event):
            self.pane['param'].flag = None
            self.pane['list'].flag = None
            self.pane['preview'].flag = None
            self.pane['param'].flagTip = None
            self.pane['list'].flagTip = None
            self.pane['preview'].flagTip = None
        state.onExit = onExit

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
            self.pane['preview'].title = 'Preview'
            self.stack.setCurrentWidget(self.preview)
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
            self.msgShow(msgBox)
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_done'])
        self.state['running'].addTransition(transition)

        transition = utility.NamedTransition('UPDATE')
        transition.setTargetState(self.state['idle_updated'])
        self.state['idle_done'].addTransition(transition)

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

    def handleOpen(self, e, fileName=None):
        """Called by toolbar action: open"""
        if fileName is None:
            (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self,
                self.title + ' - Open File',
                str(pathlib.Path.cwd()),
                'All Files (*)')
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
            'Tree files (*.tree)': fromFilter('*.tree'),
            'Vector Graphics (*.svg)': fromFilter('*.svg'),
            'Log files (*.log)': fromFilter('*.log'),
            }

        # Widget-based dialog, filters decide what files are saved
        dialog = QtWidgets.QFileDialog()
        dialog.setWindowTitle('Save with prefix')
        dialog.selectFile(str(path.stem))
        dialog.setDirectory(str(path.parent))
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
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
            print('> Saving files to folder:',saveTo)
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
            confirm = self.msgShow(msgBox)
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
            self.analysis.target = pathlib.Path(self._temp.name).as_posix()
        except Exception as exception:
            self.fail(exception)
            return

        def done(result):
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
        confirm = self.msgShow(msgBox)
        if confirm == QtWidgets.QMessageBox.Yes:
            self.launcher.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

    def handlePreview(self, item):
        """Called by file double-click"""
        try:
            path = pathlib.Path(item.file)
            self.pane['preview'].footer = path.name
            self.pane['preview'].title = 'Preview - ' + path.name
            if path.suffix == '.svg':
                self.stack.setCurrentWidget(self.graph)
                self.graphSvg.load(widgets.VectorPixmap.loadAndMap(str(path), self.colormap_graph[path.stem]))
                self.graphSvg.renderer().setAspectRatioMode(QtCore.Qt.KeepAspectRatio)
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

    def onReject(self):
        """If running, verify cancel"""
        if self.state['running'] in list(self.machine.configuration()):
            self.handleStop()
            return True
        else:
            return None

def show():
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
