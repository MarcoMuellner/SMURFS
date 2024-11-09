from typing import Optional, Any

import dash_bootstrap_components as dbc
from dash import html

def create_card_with_icon(title, body_content, color, icon_class):
    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className=f"{icon_class} me-2"),
                title
            ], className="mb-0")
        ], className=f"bg-{color}"),
        dbc.CardBody(body_content)
    ], className="shadow-sm")


from dash import html
import dash_bootstrap_components as dbc
from typing import Optional, Any


def create_input_with_validation(id_base: str, type: str, placeholder: str,
                                 required: bool = False, min: Optional[float] = None,
                                 max: Optional[float] = None, value: Any = None,
                                 help_text: Optional[str] = None) -> html.Div:
    """Create a Bootstrap input group with validation support and tooltip."""
    input_id = {"type": "text-input", "id": id_base}  # Changed type to text-input

    input_props = {
        "id": input_id,
        "type": type,
        "placeholder": placeholder,
        "value": value,
        "required": required,
        "min": min if type == "number" else None,
        "max": max if type == "number" else None,
        "invalid": False
    }

    input_props = {k: v for k, v in input_props.items() if v is not None}

    input_group = dbc.InputGroup([
        dbc.Input(**input_props),
        dbc.FormFeedback(
            "Valid input",
            type="valid",
        ),
        dbc.FormFeedback(
            "This field is required" if required else "Invalid input",
            type="invalid",
        ),
    ])

    wrapper = html.Div([input_group], className="mb-3")

    if help_text:
        return html.Div([
            wrapper,
            dbc.Tooltip(
                help_text,
                target=input_id,
                placement="right"
            )
        ])

    return wrapper


def create_card(title: str, body_content: list, color: str = "primary") -> dbc.Card:
    """Create a Bootstrap card with consistent styling.

    Args:
        title: Card header title
        body_content: List of components for card body
        color: Bootstrap color class
    """
    return dbc.Card([
        dbc.CardHeader([
            html.H4(title, className="mb-0")
        ], className=f"bg-{color} text-white"),
        dbc.CardBody(body_content)
    ])


def create_alert(title: str, message: str, color: str = "success") -> dbc.Alert:
    """Create a Bootstrap alert with consistent styling.

    Args:
        title: Alert header
        message: Alert message
        color: Bootstrap color class
    """
    return dbc.Alert(
        [
            html.H4(title, className="alert-heading"),
            html.P(message),
        ],
        color=color
    )


def validate_numeric_input(value: Any, min_val: Optional[float] = None,
                           max_val: Optional[float] = None, required: bool = False) -> bool:
    """Validate a numeric input value.

    Args:
        value: Input value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        required: Whether the input is required
    """
    if required and not value:
        return False

    if not value and not required:
        return True

    try:
        val = float(value)
        if min_val is not None and val < min_val:
            return False
        if max_val is not None and val > max_val:
            return False
        return True
    except (TypeError, ValueError):
        return False