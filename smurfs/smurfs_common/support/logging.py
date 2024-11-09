from enum import Enum
from typing import Optional, Union, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import multiprocessing as mp
from queue import Empty


class LogLevel(Enum):
    LOG = ('7;37;40', 'white')
    INFO = ('7;32;40', 'green')
    WARN = ('7;33;40', 'yellow')
    ERROR = ('7;31;40', 'red')
    STATE = ('7;34;47', 'blue')

    @classmethod
    def from_ansi(cls, ansi_code: str) -> 'LogLevel':
        for level in cls:
            if level.value[0] == ansi_code:
                return level
        return cls.LOG


@dataclass
class LogMessage:
    text: str
    level: LogLevel
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if isinstance(self.level, str):
            try:
                self.level = LogLevel[self.level.upper()]
            except KeyError:
                self.level = LogLevel.from_ansi(self.level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": f"[{self.timestamp.strftime('%H:%M:%S')}] {self.text}",
            "color": self.level.value[1],
            "timestamp": self.timestamp.isoformat()
        }


class ProcessLogger:
    def __init__(self, queue: mp.Queue):
        self.queue = queue

    def log(self, text: str, level: Union[LogLevel, str] = LogLevel.LOG):
        msg = LogMessage(text, level)
        self.queue.put(msg.to_dict())

    def log_error(self, text: str, exc_info: Optional[Exception] = None):
        self.log(text, LogLevel.ERROR)
        if exc_info:
            self.log(str(exc_info), LogLevel.ERROR)