# File: smurfs/smurfs_ui/ui_components/optional_parameters.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from smurfs.smurfs_common.preprocessing.dataloader import FluxType, Mission
from smurfs.smurfs_ui.common_ui import create_input_with_validation, create_card_with_icon

def create_optional_parameters():
    return dbc.Col([
        create_card_with_icon(
            "Optional Parameters",
            [
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Frequency Range"),
                        dbc.Row([
                            dbc.Col(
                                create_input_with_validation(
                                    "freq-min",
                                    "number",
                                    "Min frequency",
                                    help_text="Lower bound of the frequency range to analyze (in cycles/day). "
                                            "Leave empty to start from the lowest possible frequency determined by the time span of observations."
                                )
                            ),
                            dbc.Col(
                                create_input_with_validation(
                                    "freq-max",
                                    "number",
                                    "Max frequency",
                                    help_text="Upper bound of the frequency range to analyze (in cycles/day). "
                                            "Leave empty to analyze up to the Nyquist frequency, which is determined by the sampling rate."
                                )
                            )
                        ])
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Mission"),
                        dcc.Dropdown(
                            id={"type": "dropdown", "id": "mission"},
                            options=[{"label": m.name, "value": m.name} for m in Mission],
                            value=Mission.TESS.name,
                            className="mb-3"
                        ),
                        dbc.Tooltip(
                            "Select the space mission that provided the data. Each mission has specific data formats and characteristics:"
                            "\n• TESS: 2-minute or 30-minute cadence data from the TESS mission"
                            "\n• Kepler: High-precision data from the Kepler primary mission"
                            "\n• K2: Data from Kepler's extended mission",
                            target={"type": "input", "id": "mission"},
                            placement="right"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Flux Type"),
                        dcc.Dropdown(
                            id={"type": "dropdown", "id": "flux-type"},
                            options=[{"label": f.name, "value": f.name} for f in FluxType],
                            value=FluxType.PDCSAP.name,
                            className="mb-3"
                        ),
                        dbc.Tooltip(
                            "Choose the type of flux measurement to analyze:"
                            "\n• PDCSAP: Pre-searched Data Conditioning SAP flux (recommended)"
                            "\n• SAP: Simple Aperture Photometry flux"
                            "\n• RAW: Uncorrected raw flux measurements",
                            target={"type": "input", "id": "flux-type"},
                            placement="right"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Save Path"),
                        create_input_with_validation(
                            "save-path",
                            "text",
                            "Path to save results",
                            value=".",
                            help_text="Directory where analysis results will be saved. Files will include:"
                                    "\n• Frequency analysis results"
                                    "\n• Fit parameters"
                                    "\n• Diagnostic plots"
                                    "\n• Statistical summaries"
                                    "\nDefault is the current directory ('.')"
                        )
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            options=[{
                                "label": "Improve Fit",
                                "value": "improve-fit",
                                "title": "Apply additional fitting improvements after the initial analysis"
                            }],
                            id={"type": "checklist", "id": "improve-fit"},
                            switch=True,
                            value=["improve-fit"],  # Default to enabled
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        html.P(
                            "Note: Leaving optional parameters at their default values will use "
                            "optimal settings determined by the data characteristics.",
                            className="text-muted fst-italic mb-0"
                        )
                    ])
                ])
            ],
            "secondary",
            "fas fa-sliders-h"
        )
    ], width=6)