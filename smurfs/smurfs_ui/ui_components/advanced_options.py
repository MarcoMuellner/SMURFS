# File: smurfs/smurfs_ui/ui_components/advanced_options.py
import dash_mantine_components as dmc
from dash import html
from smurfs.smurfs_common.smurfs_.smurfs import FitMethod
from smurfs.smurfs_ui.common_ui import create_input_with_validation


def create_advanced_options():
    switches = [
        {
            "id": "skip-similar",
            "label": "Skip Similar Frequencies",
            "description": "Ignore regions with multiple frequencies within a small range. "
                           "Useful for avoiding over-fitting of closely spaced frequencies."
        },
        {
            "id": "skip-cutoff",
            "label": "Skip Cutoff",
            "description": "Override the default stopping behavior for frequency extraction. "
                           "Continues analysis even when SNR criteria are not met."
        },
        {
            "id": "do-pca",
            "label": "Do PCA",
            "description": "Activate Principal Component Analysis for light curve data. "
                           "Can help remove systematic trends and improve signal detection."
        },
        {
            "id": "do-psf",
            "label": "Do PSF",
            "description": "Activate Point Spread Function analysis for light curve data. "
                           "Useful for crowded fields or contaminated apertures."
        },
        {
            "id": "store-object",
            "label": "Store Object",
            "description": "Save the complete SMURFS analysis object for later use. "
                           "Enables detailed inspection and further analysis of results."
        },
        {
            "id": "apply-corrections",
            "label": "Apply Corrections",
            "description": "Apply automated corrections to the input files. "
                           "Includes outlier removal and systematic trend correction."
        }
    ]

    return dmc.Paper(
        children=[
            dmc.Group([
                html.I(className="fas fa-cogs"),
                dmc.Title("Advanced Options", order=4),
            ], justify='flex-start', gap="xs", mb="md"),

            dmc.Grid([
                # Left column - Analysis Options
                dmc.GridCol([
                    dmc.Title("Analysis Options", order=5, mb="md"),
                    dmc.Stack([
                        dmc.Tooltip(
                            multiline=True,
                            withArrow=True,
                            label = switch["description"],
                            children=[
                                dmc.Switch(
                                    id={"type": "switch", "id": switch["id"]},
                                    label=switch["label"],
                                    size="md"
                                )
                            ]
                        )
                        for switch in switches
                    ], gap="md")
                ], span=6),

                # Right column - Method Settings
                dmc.GridCol([
                    dmc.Title("Method Settings", order=5, mb="md"),
                    dmc.Stack([
                        dmc.Stack([
                            dmc.Text("Fit Method", fw=500),
                            dmc.Select(
                                id={"type": "select", "id": "fit-method"},
                                data=[{"label": m.name, "value": m.name} for m in FitMethod],
                                value=FitMethod.LMFIT.name,
                                description=(
                                    "Select the fitting method to use for frequency analysis. "
                                    "LMFIT is recommended for most cases."
                                ),
                                clearable=False,
                                searchable=False
                            )
                        ], gap="xs"),

                        dmc.Stack([
                            dmc.Text("Extend Frequencies", fw=500),
                            create_input_with_validation(
                                "extend-frequencies",
                                "number",
                                "Number of frequencies",
                                min=0,
                                value=0,
                                help_text="Number of additional frequencies to extract beyond the default cutoff"
                            )
                        ], gap="xs"),

                        dmc.Stack([
                            dmc.Text("Frequency Detection", fw=500),
                            create_input_with_validation(
                                "frequency-detection",
                                "number",
                                "Detection ratio",
                                min=0,
                                value=0,
                                help_text="Minimum ratio for frequency detection"
                            )
                        ], gap="xs")
                    ], gap="md")
                ], span=6)
            ])
        ],
        p="lg",
        radius="md",
        withBorder=True,
        shadow="sm",
        mt="md"
    )
