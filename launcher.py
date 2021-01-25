#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executable for PyInstaller
$ python pyinstaller launcher.specs
"""

import sys
import multiprocessing
import abgd.qt

if __name__ == '__main__':
    multiprocessing.freeze_support()
    abgd.qt.main.show(sys)
