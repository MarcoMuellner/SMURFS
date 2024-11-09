# File: smurfs/smurfs_ui/smurfs_helper.py
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from smurfs.smurfs_common.preprocessing.dataloader import FluxType, Mission
from smurfs.smurfs_common.smurfs_.smurfs import Smurfs, FitMethod, ImproveFitMode
from smurfs.smurfs_common.support.mprint import mprint, state as state_style, info as info_style, warn as warn_style


def validate_smurfs_inputs(values: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate SMURFS-specific input parameters.

    Args:
        values: Dictionary of input values

    Returns:
        Tuple of (is_valid, error_message)
    """
    mprint("Validating inputs...", state_style)
    required_fields = ["target", "snr", "window-size", "sigma-clip", "iters"]

    for field in required_fields:
        if not values.get(field):
            return False, f"Missing required field: {field}"

    try:
        float(values["snr"])
        float(values["window-size"])
        float(values["sigma-clip"])
        int(values["iters"])
    except ValueError:
        return False, "Invalid numeric input"

    return True, None


def create_smurfs_instance(values: Dict[str, Any]) -> Smurfs:
    """Create and configure a SMURFS instance from input values.

    Args:
        values: Dictionary of input values
    """
    mprint(f"Creating SMURFS instance with parameters:", info_style)
    #nicely print values
    values_string = "\n".join([f"  - {key}: {value}" for key, value in values.items()])
    mprint(values_string, info_style)
    advanced_options = values.get("advanced-options", [])

    smurfs = Smurfs(
        target=values["target"],
        flux_type=FluxType[values["flux-type"]],
        sigma_clip=float(values["sigma-clip"]),
        iters=int(values["iters"]),
        do_pca="do-pca" in advanced_options,
        do_psf="do-psf" in advanced_options,
        apply_file_correction="apply-corrections" in advanced_options,
        mission=Mission[values["mission"]]
    )

    # Log configuration details
    mprint(f"Target: {values['target']}", info_style)
    mprint(f"Flux Type: {values['flux-type']}", info_style)
    mprint(f"Mission: {values['mission']}", info_style)
    mprint(f"Sigma Clip: {values['sigma-clip']}", info_style)
    mprint(f"Iterations: {values['iters']}", info_style)
    if advanced_options:
        mprint("Advanced options enabled:", info_style)
        for option in advanced_options:
            mprint(f"  - {option}", info_style)

    return smurfs


def _safe_float(value: Any, default: float = 0.0) -> Optional[float]:
    """Safely convert value to float, returning default if invalid."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any, default: int = 0) -> Optional[int]:
    """Safely convert value to int, returning default if invalid."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))  # handle both "1" and "1.0"
    except (ValueError, TypeError):
        return default


def run_smurfs_analysis(smurfs: Smurfs, values: Dict[str, Any]) -> None:
    """Run SMURFS analysis with the given parameters.

    Args:
        smurfs: Configured SMURFS instance
        values: Dictionary of input values
    """
    mprint("Starting SMURFS analysis...", state_style)
    advanced_options = values.get("advanced-options", [])
    improve_fit = "improve-fit" in advanced_options

    # Get the fit method with fallback to LMFIT
    fit_method = FitMethod.LMFIT  # Default
    try:
        method_name = values.get("fit-method", FitMethod.LMFIT.name)
        fit_method = FitMethod[method_name]
    except (KeyError, TypeError):
        mprint(f"Warning: Invalid fit method specified, using {fit_method.name}", warn_style)

    # Log analysis parameters
    mprint(f"SNR: {values['snr']}", info_style)
    mprint(f"Window Size: {values['window-size']}", info_style)
    mprint(f"Fit Method: {fit_method.name}", info_style)

    if values.get("freq-min"):
        mprint(f"Minimum Frequency: {values['freq-min']}", info_style)
    if values.get("freq-max"):
        mprint(f"Maximum Frequency: {values['freq-max']}", info_style)

    extend_frequencies = _safe_int(values.get("extend-frequencies"), 0)
    frequency_detection = _safe_float(values.get("frequency-detection"), 0.0)

    if extend_frequencies > 0:
        mprint(f"Extend Frequencies: {extend_frequencies}", info_style)
    if frequency_detection > 0:
        mprint(f"Frequency Detection: {frequency_detection}", info_style)
    mprint(f"Improve Fit: {'enabled' if improve_fit else 'disabled'}", info_style)

    smurfs.run(
        snr=float(values["snr"]),
        window_size=float(values["window-size"]),
        f_min=_safe_float(values.get("freq-min"), None),
        f_max=_safe_float(values.get("freq-max"), None),
        skip_similar="skip-similar" in advanced_options,
        similar_chancel=not "skip-cutoff" in advanced_options,
        extend_frequencies=extend_frequencies,
        improve_fit=improve_fit,
        mode=fit_method,
        frequency_detection=frequency_detection
    )

    if improve_fit:
        mprint("Improving fit results...", state_style)
        smurfs.improve_result()

    save_path = Path(values.get("save-path", ".") or ".")
    store_object = "store-object" in advanced_options

    mprint(f"Saving results to: {save_path}", state_style)
    if store_object:
        mprint("Storing SMURFS object for later use", info_style)

    smurfs.save(save_path, store_object)
    mprint("Analysis completed successfully", state_style)