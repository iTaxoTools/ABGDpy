#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executable for PyInstaller
$ python pyinstaller launcher.specs
"""

import sys
import multiprocessing
import src.abgd.qt

if __name__ == '__main__':
    multiprocessing.freeze_support()
    src.abgd.qt.main.show(sys)
