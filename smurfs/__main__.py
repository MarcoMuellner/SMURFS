import sys
import warnings

import typer
from typing import Optional, Annotated
from pathlib import Path

from smurfs.preprocessing.dataloader import FluxType, Mission
from smurfs.smurfs_.smurfs import Smurfs, FitMethod, ImproveFitMode

app = typer.Typer()

class FrequencyRange:
    def __init__(self, min_value: Optional[float], max_value: Optional[float]):
        self.min_value = min_value
        self.max_value = max_value

    @property
    def min(self):
        return self.min_value if self.min_value is not None else float('-inf')

    @property
    def max(self):
        return self.max_value if self.max_value is not None else float('inf')

    def __str__(self):
        return f"FrequencyRange(min={self.min_value}, max={self.max_value})"

def parse_frequency_range(value: str) -> FrequencyRange:
    if value is None:
        return None
    parts = value.split(',')
    if len(parts) != 2:
        raise ValueError("FrequencyRange must be in the format 'min,max', 'min,', or ',max'")
    min_val = float(parts[0]) if parts[0] else None
    max_val = float(parts[1]) if parts[1] else None
    return FrequencyRange(min_val, max_val)

@app.command()
def main(
        target: str = typer.Argument(..., help="Target to analyze. Can be a star name or a filename."),
        snr: float = typer.Argument(..., help="Lower bound signal to noise ratio for frequencies."),
        window_size: float = typer.Argument(..., help="Window size used to get the SNR for a given frequency."),
        frequency_range: Annotated[Optional[FrequencyRange], typer.Option(
            "--frequency-range",
            "-fr",
            help="Restrict analysis to a given range in the frequency spectrum. Format: 'min,max' or 'min,' or ',max'",
            parser=parse_frequency_range
        )] = None,
        skip_similar_frequencies: bool = typer.Option(False, "--skip-similar-frequencies", "-ssa",
                                                      help="Ignore regions with multiple frequencies within a small range."),
        skip_cutoff: bool = typer.Option(False, "--skip-cutoff", "-sc",
                                         help="Override the default stopping behavior for frequency extraction."),
        extend_frequencies: int = typer.Option(0, "--extend-frequencies", "-ef",
                                               help="Extend analysis by n frequencies."),
        frequency_detection: Optional[float] = typer.Option(None, "--frequency-detection", "-fd",
                                                            help="Ratio for comparing found frequency to original periodogram."),
        improve_fit_mode: ImproveFitMode = typer.Option(ImproveFitMode.ALL, "--improve-fit-mode", "-imf",
                                                        help="Mode for improving frequency fits."),
        fit_method: FitMethod = typer.Option(FitMethod.LMFIT, "--fit-method", "-fm", help="Fitting library to use."),
        flux_type: FluxType = typer.Option(FluxType.PDCSAP, "--flux-type", "-ft",
                                           help="Type of flux data product to use."),
        do_pca: bool = typer.Option(False, "--do-pca", "-pca", help="Activate PCA analysis for LC data."),
        do_psf: bool = typer.Option(False, "--do-psf", "-psf", help="Activate PSF analysis for LC data."),
        store_object: bool = typer.Option(False, "--store-object", "-so",
                                          help="Store the SMURFS object in the results."),
        save_path: Path = typer.Option(Path("."), "--save-path", "-sp", help="Save path for the analysis results."),
        interactive: bool = typer.Option(False, "--interactive", "-i", help="Start an iPython shell after analysis."),
        mission: Mission = typer.Option(Mission.TESS, "--mission", "-m", help="Mission to consider."),
        sigma_clip: float = typer.Option(4.0, "--sigma-clip", "-cl", help="Sigma for the sigma clipping."),
        iters: int = typer.Option(1, "--iters", "-it", help="Iterations for the sigma clipping."),
        apply_corrections: bool = typer.Option(False, "--apply-corrections", "-ac", help="Apply corrections to files."),
):
    """
    SMURFS: Stellar Measurements Under Relative Fairness Standards

    This tool analyzes stellar data from various missions or custom files to extract frequency information.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        s = Smurfs(
            target=target,
            flux_type=flux_type,
            sigma_clip=sigma_clip,
            iters=iters,
            do_pca=do_pca,
            do_psf=do_psf,
            apply_file_correction=apply_corrections,
            mission=mission,
        )

        improve_fit = improve_fit_mode == ImproveFitMode.ALL
        f_min = frequency_range.min if frequency_range else None
        f_max = frequency_range.max if frequency_range else None

        s.run(snr=snr, window_size=window_size, f_min=f_min, f_max=f_max,
              skip_similar=skip_similar_frequencies, similar_chancel=not skip_cutoff
              , extend_frequencies=extend_frequencies, improve_fit=improve_fit
              , mode=fit_method, frequency_detection=frequency_detection)

        if improve_fit:
            s.improve_result()

        s.save(save_path, store_object)

if __name__ == "__main__" or __name__ == "smurfs.__main__":
    app()

sys.exit(0)