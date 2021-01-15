from multiprocessing import Process

from . import _abgdc

def bar(v):
    return v-42

def run(dictionary):
    """
    Must always use a seperate process to launch the ABGD core,
    since it uses exit(1) without freeing allocated memory.
    """
    p = Process(target=_abgdc.main, args=(dictionary,))
    p.start()
    p.join()
    if p.exitcode != 0:
        raise RuntimeError('ABGD internal error, please check logs.')
