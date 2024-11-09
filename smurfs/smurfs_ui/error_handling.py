# File: smurfs/smurfs_ui/error_handling.py
from typing import Optional, Tuple
import dash_mantine_components as dmc
from dash import html


def create_error_alert(error: Exception, traceback: str) -> dmc.Alert:
    """Create a formatted error alert with traceback."""
    return dmc.Alert(
        children=[
            dmc.Text(str(error), size="sm"),
            dmc.Space(h=10),
            dmc.Prism(
                traceback,
                language="python",
                withLineNumbers=True,
                copyLabel="Copy traceback",
                copiedLabel="Copied!",
                noCopy=False,
            )
        ],
        title="Error",
        color="red",
        variant="filled",
        withCloseButton=True
    )


def create_validation_error(message: str) -> dmc.Alert:
    """Create a validation error alert."""
    return dmc.Alert(
        children=[
            dmc.Text(message, size="sm")
        ],
        title="Validation Error",
        color="yellow",
        variant="filled",
        withCloseButton=True
    )


def format_error_message(error: Exception, include_type: bool = True) -> str:
    """Format an error message for display."""
    if include_type:
        return f"{error.__class__.__name__}: {str(error)}"
    return str(error)


def validate_numeric_value(
        value: Optional[str],
        field_name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        required: bool = False
) -> Tuple[bool, Optional[str]]:
    """Validate a numeric input value with detailed error message."""
    if not value and not required:
        return True, None

    if not value and required:
        return False, f"{field_name} is required"

    try:
        num_value = float(value)
        if min_val is not None and num_value < min_val:
            return False, f"{field_name} must be greater than {min_val}"
        if max_val is not None and num_value > max_val:
            return False, f"{field_name} must be less than {max_val}"
        return True, None
    except ValueError:
        return False, f"{field_name} must be a valid number"