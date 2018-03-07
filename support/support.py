import os

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