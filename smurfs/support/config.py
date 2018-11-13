from smurfs.support.singleton import Singleton
from enum import Enum

class UncertaintiesMode(Enum):
    none = "None"
    montgomery = "Montgomery"
    fit = "Fit"

    @staticmethod
    def content():
        return [e.value for e in UncertaintiesMode]


@Singleton
class Config:

    def __init__(self,*args):
        self.uncertaintiesMode = UncertaintiesMode.none.value
        pass

    @property
    def uncertaintiesMode(self):
        return self._errorMode

    @uncertaintiesMode.setter
    def uncertaintiesMode(self, val : UncertaintiesMode):
        if not isinstance(val, UncertaintiesMode) and val not in UncertaintiesMode.content():
            raise ValueError("Please pass a valid Errormode!")

        self._errorMode = val

def conf() -> Config:
    return Config.ins()