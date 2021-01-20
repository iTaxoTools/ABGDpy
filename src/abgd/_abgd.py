from multiprocessing import Process

import tempfile as _tempfile
import shutil as _shutil

from . import _abgdc

def bar(v):
    return v-42

class BarcodeAnalysis():
    """
    Container for input/output of ABGD core.
    """

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __init__(self, file, params):
        """
        """
        self.file = file
        self.params = params
        self.results = None

    def fetch(self, destination):
        """
        Copy files from tempdir to given dir.
        """
        _shutil.copytree(self.results.name, destination)

    def run(self):
        """
        Run the ABGD core with given params,
        save results to a temporary directory.
        """
        temp = _tempfile.TemporaryDirectory(prefix='abgd')
        self.params['file'] = self.file
        # self.params['out'] = temp.name
        self.params['out'] = '.'
        _abgdc.main(self.params)
        self.results = temp
        del self.params['file']
        del self.params['out']


def worker(analysis):
    """
    Called by run() on a new process
    """
    analysis.run()
    print(analysis.results.name)
    # analysis.fetch('/tmp/potato/')


def launch(analysis):
    """
    Should always use a seperate process to launch the ABGD core,
    since it uses exit(1) and doesn't always free allocated memory.
    """
    p = Process(target=worker, args=(analysis,))
    p.start()
    p.join()
    if p.exitcode != 0:
        raise RuntimeError('ABGD internal error, please check logs.')


def run(dictionary):
    p = Process(target=_abgdc.main, args=(dictionary,))
    p.start()
    p.join()
    if p.exitcode != 0:
        raise RuntimeError('ABGD internal error, please check logs.')
