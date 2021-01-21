from multiprocessing import Process

import importlib.resources
import tempfile as _tempfile
import shutil as _shutil

from . import _abgdc
from . import param

class BarcodeAnalysis():
    """
    Container for input/output of ABGD core.
    """

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __init__(self, file):
        """
        """
        self.file = file
        self.target = None
        self.results = None
        with importlib.resources.open_text(__package__, 'params.json') as data:
            self.param = param.ParamList(data)

    def fetch(self, destination):
        """
        Copy results as a new directory.
        """
        if self.results is None:
            raise RuntimeError('No results to fetch.')
        _shutil.copytree(self.results, destination)

    def run(self):
        """
        Run the ABGD core with given params,
        save results to a temporary directory.
        """
        kwargs = self.param.as_dictionary()
        kwargs['file'] = self.file
        if self.target is not None:
            kwargs['out'] = self.target
        print(kwargs)
        _abgdc.main(kwargs)
        self.results = self.target


def worker(analysis):
    """
    Called by launch() on a new process
    """
    analysis.run()
    print('Analysis complete:', analysis.results)

def launch(analysis):
    """
    Should always use a seperate process to launch the ABGD core,
    since it uses exit(1) and doesn't always free allocated memory.
    Save results on a temporary directory, use fetch() to retrieve them.
    """
    # When the last reference of TemporaryDirectory is gone,
    # the directory is automatically cleaned up, so keep it here.
    analysis._temp = _tempfile.TemporaryDirectory(prefix='abgd_')
    analysis.target = analysis._temp.name
    p = Process(target=worker, args=(analysis,))
    p.start()
    p.join()
    if p.exitcode != 0:
        raise RuntimeError('ABGD internal error, please check logs.')
    # Success, update analysis object for parent process
    analysis.results = analysis.target
