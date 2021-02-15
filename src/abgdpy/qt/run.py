"""Entry point for Qt GUI"""

import sys
import multiprocessing
from . import main as qt_main

def main():
    """Display the graphical interface."""
    # force spawning on linux for debugging
    # multiprocessing.set_start_method('spawn')
    if len(sys.argv) <= 2:
        a = qt_main.show()
    else:
        print('Usage: abgd-qt FILE')
        print('Ex:    abgd-qt tests/test.fas')
