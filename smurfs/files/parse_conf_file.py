import json

str_snr_criterion = "SNR criterion"
str_window_size = "Window size"

class ConfFileError(Exception):
    """
    Errorclass for problems with conf file
    """
    def __init__(self,message):
        super().__init__(message)

class ConfFile:
    def __init__(self,file_name : str):
        if not file_name.endswith(".json"):
            raise ConfFileError("Configuration files need to be json files and end with .json!")

        with open(file_name,'r') as f:
            conf_data = json.loads(f)

