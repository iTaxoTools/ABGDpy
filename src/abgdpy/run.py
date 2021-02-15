"""Console entry point"""

import sys
from . import core

#! This should be expanded to accept all arguments
def main():
    """Anayze given file"""
    if len(sys.argv) == 2:
        print(' ')
        a=core.BarcodeAnalysis(sys.argv[1])
        core.launch(a)
        # a.fetch
    else:
        print('Usage: abgd FILE')
        print('Ex:    abgd tests/test.fas')
