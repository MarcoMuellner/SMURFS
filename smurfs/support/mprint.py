from smurfs.support.settings import Settings

log = '7;37;40'
info = '7;32;40'
warn = '7;33;40'
error = '7;31;40'
state = '7;34;47'


def mprint(text: str, type: str):
    if not Settings.quiet:
        print(f'\x1b[{type}m {text} \x1b[0m')

def ctext(text : str, type : str)->str:
    return f'\x1b[{type}m {text} \x1b[0m'
