from smurfs.support.singleton import Singleton
from enum import Enum

class UncertaintyMode(Enum):
    none = "None"
    montgomery = "Montgomery"
    fit = "Fit"

    @staticmethod
    def content():
        return [e.value for e in UncertaintyMode]


@Singleton
class Config:

    def __init__(self,*args):
        self.uncertaintiesMode = UncertaintyMode.none.value
        pass

    @property
    def uncertaintiesMode(self):
        return self._errorMode

    @uncertaintiesMode.setter
    def uncertaintiesMode(self, val : UncertaintyMode):
        if not isinstance(val, UncertaintyMode) and val not in UncertaintyMode.content():
            raise ValueError("Please pass a valid Errormode!")

        self._errorMode = val

def conf() -> Config:
    return Config.ins()