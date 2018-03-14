import os
import time
from stem.util import term

import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

class cd:
    """
    Directory changer. can change the directory using the 'with' keyword, and returns to the previous path
    after leaving intendation. Example:

    with cd("some/path/to/go"): # changing dir
        foo()
        ...
        bar()
    #back to old dir
    """
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

printTimer = False

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            if printTimer:
                print(term.format('%r  %2.2f ms' % \
                      (method.__name__, (te - ts) * 1000),term.Color.BLUE))
        return result
    return timed

processList = {}
multiProcessing = False

def addProcess(name,p):
    p.start()
    if multiProcessing:
        processList[name]=p
    else:
        p.join()

def waitForProcessesFinished():
    for name,process in processList.items():
        print("Waiting for "+name+" to end")
        process.join()