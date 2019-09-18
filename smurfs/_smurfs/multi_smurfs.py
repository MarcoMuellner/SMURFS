from typing import List, Union
import numpy as np
from lightkurve import LightCurve, TessLightCurve
import os
from multiprocessing import Pool,cpu_count


from smurfs.preprocess.tess import download_lc
from smurfs.preprocess.file import load_file
from smurfs.support.mprint import *
import smurfs.support.mprint
from smurfs._smurfs.smurfs import Smurfs


class MultiSmurfs:
    def __init__(self, file_list: List[str] = None, time_list: List[np.ndarray] = None
                 , flux_list: List[np.ndarray] = None, target_list: List[str] = None,
                 flux_types: Union[List[str], str] = 'PDCSAP', label_list: List[str] = None):

        self.s_list: List[Smurfs] = []

        if target_list is not None:

            if isinstance(flux_types, list) and len(flux_types) != len(target_list):
                raise ValueError(ctext("Length of flux_list types and target list must be equal!", error))
            elif not isinstance(flux_types, list):
                flux_types = [flux_types for _ in range(len(target_list))]

            if isinstance(label_list, list) and len(label_list) != len(target_list):
                raise ValueError(ctext("Length of label list and target list must be equal!", error))
            elif not isinstance(label_list, list):
                label_list = [label_list for _ in range(len(target_list))]

            for target, flux_type, label in zip(target_list, flux_types, label_list):
                self.s_list.append(Smurfs(target_name=target, flux_type=flux_list))

        elif time_list is None and flux_list is None and file_list is None:

            raise AttributeError(
                ctext("You need to either pass a target path or time_list and flux_list of the lightcurve object",
                      error))

        elif time_list is not None and flux_list is not None:

            if len(time_list) != len(flux_list):
                raise ValueError(ctext("Length of times and fluxes need to be equal!", error))

            if isinstance(label_list, list) and len(label_list) != len(flux_list):
                raise ValueError(ctext("Length of labels must be equal to flux- and time lists", error))
            elif not isinstance(label_list, list):
                label_list = [label_list for _ in range(len(target_list))]

            for time, flux, label in zip(time_list, flux_list, label_list):
                self.s_list.append(Smurfs(time=time, flux=flux, label=label))

        elif file_list is not None:

            for file in file_list:
                self.s_list.append(Smurfs(file=file))
        else:
            raise AttributeError(
                ctext("You need to either pass a target path or time_list and flux_list of the lightcurve object",
                      error))

    def run(self, snr: float = 4, window_size: float = 2, f_min: float = None, f_max: float = None,
            skip_similar: bool = False, similar_chancel=True, extend_frequencies: int = 0,improve_fit = True,
            mode='lmfit',workers : int= cpu_count()):
            #todo allow for differen parameters for different runs

            param_list = [(snr,window_size,f_min,f_max,skip_similar,similar_chancel
                           ,extend_frequencies,improve_fit,mode) for i in range(len(self.s_list))]

            mprint.quiet = True
            p = Pool(workers)

            for s,param in zip(self.s_list,param_list):
                p.starmap(s,param)

    def save(self,save_path : str, store_obj = False):
        for s in self.s_list:
            s.save(save_path,store_obj)





