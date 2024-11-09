# File: smurfs/smurfs_common/support/mprint.py
from enum import Enum
from typing import Optional
from smurfs.smurfs_common.support.logging import LogLevel, ProcessLogger
from smurfs.smurfs_common.support.settings import Settings


class LogType(Enum):
    LOG = ('7;37;40', LogLevel.LOG)
    INFO = ('7;32;40', LogLevel.INFO)
    WARN = ('7;33;40', LogLevel.WARN)
    ERROR = ('7;31;40', LogLevel.ERROR)
    STATE = ('7;34;47', LogLevel.STATE)


class MPrinter:
    _instance = None

    def __init__(self, logger: Optional[ProcessLogger] = None):
        self.logger = logger

    @classmethod
    def initialize(cls, logger: ProcessLogger):
        cls._instance = cls(logger)

    @classmethod
    def get_instance(cls) -> 'MPrinter':
        if cls._instance is None:
            raise RuntimeError("MPrinter not initialized")
        return cls._instance

    def print(self, text: str, type: str):
        try:
            log_type = LogType[type.upper()]
            ansi_code = log_type.value[0]
            log_level = log_type.value[1]
        except KeyError:
            ansi_code = type
            log_level = LogLevel.LOG

        if not Settings.quiet:
            print(f'\x1b[{ansi_code}m {text} \x1b[0m')

        if self.logger:
            self.logger.log(text, log_level)


def mprint(text: str, type: str):
    MPrinter.get_instance().print(text, type)

def ctext(text : str, type : str)->str:
    return f'\x1b[{type}m {text} \x1b[0m'


# Convenience constants for backward compatibility
log = LogType.LOG.value[0]
info = LogType.INFO.value[0]
warn = LogType.WARN.value[0]
error = LogType.ERROR.value[0]
state = LogType.STATE.value[0]