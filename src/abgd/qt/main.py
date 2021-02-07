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
        data = self.loadAndMap(fileName, colormap)

        renderer = QtSvg.QSvgRenderer(data)
        size = renderer.defaultSize() if size is None else size
        super().__init__(size)
        self.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self)
        renderer.render(painter)
        painter.end()

    @staticmethod
    def loadAndMap(fileName, colormap):
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QIODevice.ReadOnly):
            raise FileNotFoundError('Vector resource not found: ' + fileName)
        text = file.readAll().data().decode()
        file.close()

        # old code that also checks prefixes
        # if colormap is not None:
        #     # match options fill|stroke followed by a key color
        #     regex = '(?P<prefix>(fill|stroke)\:)(?P<color>' + \
        #         '|'.join(map(re.escape, colormap.keys()))+')'
        #     # replace just the color according to colormap
        #     print(regex)
        #     text = re.sub(regex, lambda mo: mo.group('prefix') + colormap[mo.group('color')], text)

        if colormap is not None:
            regex = '(?P<color>' + '|'.join(map(re.escape, colormap.keys()))+')'
            text = re.sub(regex, lambda mo: colormap[mo.group('color')], text)

        return QtCore.QByteArray(text.encode())

class VIcon(QtGui.QIcon):
    """A colored vector icon"""
    def __init__(self, fileName, colormap_modes):
        """Create pixmaps with colormaps matching the dictionary modes"""
        super().__init__()
        for mode in colormap_modes.keys():
            self.addPixmap(VPixmap(fileName,colormap=colormap_modes[mode]), mode)

class VLine(QtWidgets.QFrame):
    """Vertical line separator"""
    def __init__(self, width=2):
        super().__init__()
        self.setFixedWidth(width)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setStyleSheet("""
            background: palette(Mid);
            border: none;
            margin: 4px;
            """)

class ScalingImage(QtWidgets.QLabel):
    """Keep aspect ratio, width adjusts with height"""
    def __init__(self, pixmap=None):
        """Remember given pixmap and ratio"""
        super().__init__()
        self.setScaledContents(False)
        self._polished = False
        self._logo = None
        self._ratio = 0
        if pixmap is not None:
            self.logo = pixmap

    @property
    def logo(self):
        return self._logo

    @logo.setter
    def logo(self, logo):
        """Accepts logo as a new pixmap to show"""
        self._logo = logo
        self._ratio = logo.width()/logo.height()
        self._scale()

    def _scale(self):
        """Create new pixmap to match new sizes"""
        if self._logo is None:
            return
        h = self.height()
        w = h * self._ratio
        self.setPixmap(self._logo.scaled(w, h,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def minimumSizeHint(self):
        return QtCore.QSize(1, 1)

    def sizeHint(self):
        if self._polished is True and self._ratio != 0:
            h = self.height()
            return QtCore.QSize(h * self._ratio, h)
        else:
            return QtCore.QSize(1, 1)

    def resizeEvent(self, event):
        self._scale()
        super().resizeEvent(event)

    def event(self, ev):
        """Let sizeHint know that sizes are now real"""
        if ev.type() == QtCore.QEvent.PolishRequest:
            self._polished = True
            self.updateGeometry()
        return super().event(ev)


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

        self._description = None
        self._citation = None
        self._logoTool = None

        self.logoSize = 64

        self.draw()

    def draw(self):
        """ """
        self.setStyleSheet("""
            Header {
                background: palette(Light);
                border-top: 2px solid palette(Mid);
                border-bottom: 1px solid palette(Dark);
                }
            """)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        self.labelDescription = QtWidgets.QLabel('DESCRIPTION')
        self.labelDescription.setStyleSheet("""
            color: palette(Text);
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
            """)

        self.labelCitation = QtWidgets.QLabel('CITATION')
        self.labelCitation.setStyleSheet("""
            color: palette(Shadow);
            font-size: 12px;
            """)

        self.labelLogoTool = QtWidgets.QLabel()
        self.labelLogoTool.setAlignment(QtCore.Qt.AlignCenter)

        self.labelLogoProject = ScalingImage()
        layoutLogoProject = QtWidgets.QHBoxLayout()
        layoutLogoProject.addWidget(self.labelLogoProject)
        layoutLogoProject.setContentsMargins(2,4,2,4)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(32,32))
        self.toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.toolbar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 2px;
                }
            QToolButton {
                color: palette(ButtonText);
                background: transparent;
                border: 2px solid transparent;
                border-radius: 3px;
                font-size: 14px;
                min-width: 50px;
                min-height: 60px;
                padding: 6px 0px 0px 0px;
                margin: 4px 0px 4px 0px;
                }
            QToolButton:hover {
                background: palette(Window);
                border: 2px solid transparent;
                }
            QToolButton:pressed {
                background: palette(Midlight);
                border: 2px solid palette(Mid);
                border-radius: 3px;
                }
            """)

        labels = QtWidgets.QVBoxLayout()
        labels.addSpacing(4)
        labels.addWidget(self.labelDescription)
        labels.addWidget(self.labelCitation)
        labels.addSpacing(4)
        labels.setSpacing(4)

        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(18)
        layout.addWidget(self.labelLogoTool)
        layout.addSpacing(12)
        layout.addWidget(VLine())
        layout.addSpacing(12)
        layout.addLayout(labels, 0)
        layout.addSpacing(12)
        layout.addWidget(VLine())
        layout.addSpacing(8)
        layout.addWidget(self.toolbar, 0)
        layout.addStretch(1)
        layout.addWidget(VLine())
        layout.addLayout(layoutLogoProject, 0)
        # layout.addWidget(self.labelLogoProject)
        layout.addSpacing(2)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

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

    @logoTool.setter
    def logoTool(self, logo):
        self.labelLogoTool.setPixmap(logo)
        self._logoTool = logo

    @property
    def logoProject(self):
        return self.labelLogoProject.logo

    @logoProject.setter
    def logoProject(self, logo):
        self.labelLogoProject.logo = logo


class Panel(QtWidgets.QWidget):
    """
    A stylized panel with title, footer and body.
    Set `self.title`, `self.footer` and `self.flag` with text.
    Use `self.body.addWidget()`` to populate the pane.
    """
    def __init__(self, parent):
        """Initialize internal vars"""
        super().__init__(parent=parent)
        self._title = None
        self._warn = None
        self._foot = None

        # if not hasattr(parent, '_pane_foot_height'):
        #     parent._pane_foot_height = None
        self.draw()

    def draw(self):
        """ """
        self.labelTitle = QtWidgets.QLabel('TITLE GO HERE')
        self.labelTitle.setIndent(4)
        self.labelTitle.setMargin(2)
        self.labelTitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                color: palette(Light);
                background: palette(Shadow);
                border-right: 1px solid palette(Dark);
                border-bottom: 2px solid palette(Dark);
                border-bottom-left-radius: 1px;
                border-top-right-radius: 1px;
                padding-top: 2px;
                }
            QLabel:disabled {
                background: palette(Mid);
                border-right: 1px solid palette(Midlight);
                border-bottom: 2px solid palette(Midlight);
                }
            """)

        self.labelFlag = QtWidgets.QLabel('')
        self.labelFlag.setVisible(False)
        self.labelFlag.setIndent(4)
        self.labelFlag.setMargin(2)
        self.labelFlag.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                color: palette(Light);
                background: palette(Mid);
                border-right: 1px solid palette(Midlight);
                border-bottom: 2px solid palette(Midlight);
                border-bottom-left-radius: 1px;
                border-top-right-radius: 1px;
                padding-top: 1px;
                }
            QLabel:disabled {
                background: palette(Midlight);
                border-right: 1px solid palette(Light);
                border-bottom: 2px solid palette(Light);
                }
            """)

        # To be filled by user
        self.body = QtWidgets.QVBoxLayout()

        self.labelFoot = QtWidgets.QLabel('FOOTER')
        self.labelFoot.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFoot.setStyleSheet("""
            QLabel {
                color: palette(Shadow);
                background: palette(Window);
                border: 1px solid palette(Mid);
                padding: 5px 10px 5px 10px;
                }
            QLabel:disabled {
                color: palette(Mid);
                background: palette(Window);
                border: 1px solid palette(Mid);
                }
            """)


        layoutTop = QtWidgets.QHBoxLayout()
        layoutTop.addWidget(self.labelTitle, 1)
        layoutTop.addWidget(self.labelFlag, 0)
        layoutTop.setSpacing(4)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layoutTop, 0)
        layout.addLayout(self.body, 1)
        layout.addWidget(self.labelFoot, 0)
        layout.setSpacing(6)
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
    def flag(self):
        return self._warn

    @flag.setter
    def flag(self, flag):
        if flag is not None:
            self.labelFlag.setText(flag)
            self.labelFlag.setVisible(True)
        else:
            self.labelFlag.setVisible(False)
        self._warn = flag

    @property
    def footer(self):
        return self._foot

    @footer.setter
    def footer(self, footer):
        self.labelFoot.setText(footer)
        self._foot = footer

class ToolDialog(QtWidgets.QDialog):
    """
    For use as the main window of a tool.
    Handles notification sub-dialogs.
    Asks for verification before closing.
    """
    def reject(self):
        """Called on dialog close or <ESC>"""
        if self.onReject() is not None:
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Are you sure you want to quit?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        confirm = self.msgShow(msgBox)
        if confirm == QtWidgets.QMessageBox.Yes:
            super().reject()

    def onReject(self):
        """
        Overload this to handle reject events.
        Return None to continue with rejection, anything else to cancel.
        """
        return None

    def msgCloseAll(self):
        """Rejects any open QMessageBoxes"""
        for widget in self.children():
            if widget.__class__ == QtWidgets.QMessageBox:
                widget.reject()

    def msgShow(self, dialog):
        """Exec given QMessageBox after closing all others"""
        self.msgCloseAll()
        return dialog.exec()

    def fail(self, exception):
        """Show exception dialog"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('An exception occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        self.msgShow(msgBox)
        logger = logging.getLogger()
        logger.error(str(exception))

class Main(ToolDialog):
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
            VIcon.Normal: {
                '#000000': color['black'],
                '#ff0000': color['red'],
                },
            VIcon.Disabled: {
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
            'ABGD by G. Achaz, S. Brouillet, BIONJ by O. Gascuel' + '\n'
            'Python wrapper by S. Patmanidis'
        )

        self.line = QtWidgets.QFrame()
        self.line.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.line.setStyleSheet("""
            QFrame {
                background-color: palette(Midlight);
                border-style: solid;
                border-width: 1px 0px 1px 0px;
                border-color: palette(Mid);
                }
            """)

        self.line.icon = QtWidgets.QLabel()
        self.line.icon.setPixmap(VPixmap(':/icons/arrow-right.svg',
            colormap=self.colormap_icon_light))
        self.line.icon.setStyleSheet('border-style: none;')

        self.line.file = QtWidgets.QLineEdit()
        self.line.file.setPlaceholderText('Open a file to start')
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
        # self.paramWidget.setStyleSheet("background: blue;")
        self.paramWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        self.paramWidget.setContentsMargins(0, 0, 0, 0)
        self.paramWidget.paramChanged.connect(
            lambda e: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        self.pane['param'] = Panel(self)
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

        self.pane['list'] = Panel(self)
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

        self.pane['preview'] = Panel(self)
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
            self.pane['param'].flag = 'UPDATED'
        state.onEntry = onEntry
        def onExit(event):
            self.pane['param'].flag = None
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
                self.graphSvg.load(VPixmap.loadAndMap(str(path), self.colormap_graph[path.stem]))
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
