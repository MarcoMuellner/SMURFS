# File: smurfs/smurfs_ui/common_ui.py
from typing import Optional, Any, Union
import dash_mantine_components as dmc
from dash import html


def create_input_with_validation(
        id_base: str,
        type: str,
        placeholder: str,
        required: bool = False,
        min: Optional[float] = None,
        max: Optional[float] = None,
        value: Any = None,
        help_text: Optional[str] = None
) -> Union[dmc.TextInput, dmc.NumberInput, dmc.Tooltip]:
    """Create a Mantine input with validation support and description."""
    input_id = {"type": "text-input", "id": id_base}

    common_props = {
        "id": input_id,
        "placeholder": placeholder,
        "required": required,
        "style": {"marginBottom": "1rem", "width": "300px"},
        "value": value
    }

    if type == "number":
        object = dmc.NumberInput(
            **common_props,
            min=min if min is not None else -1e9,
            max=max if max is not None else 1e9,
            stepHoldDelay=500,
            stepHoldInterval=100
        )
    else:
        object = dmc.TextInput(**common_props)

    if help_text is not None:
        return dmc.Tooltip(
            multiline=True,
            withArrow=True,
            label=help_text,
            children=[object]
        )
    else:
        return object


def create_card_with_icon(title: str, children: list, color: str, icon_class: str) -> dmc.Paper:
    """Create a Mantine paper with an icon."""
    return dmc.Paper(
        children=[
            dmc.Group([
                dmc.Group([
                    html.I(className=icon_class),
                    dmc.Title(title, order=4),
                ], gap="xs"),
            ], justify="apart", mb="md"),  # Changed position to justify
            *children
        ],
        p="lg",
        radius="md",
        withBorder=True,
        shadow="sm"
    )


def create_notification(
        title: str,
        message: str,
        color: str = "blue",
        icon: Optional[str] = None
) -> dict:
    """Create a Mantine notification configuration."""
    return {
        "title": title,
        "message": message,
        "color": color,
        "icon": icon,
        "autoClose": 5000
    }