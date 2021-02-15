#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executable for PyInstaller
$ python pyinstaller launcher.specs
"""

import sys
import multiprocessing
import src.abgdpy.qt

if __name__ == '__main__':
    multiprocessing.freeze_support()
    src.abgdpy.qt.main.show()
