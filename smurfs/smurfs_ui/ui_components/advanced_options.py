# File: smurfs/smurfs_ui/ui_components/advanced_options.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from smurfs.smurfs_common.smurfs_.smurfs import FitMethod
from smurfs.smurfs_ui.common_ui import create_input_with_validation, create_card_with_icon


def create_advanced_options():
    return dbc.Row([
        dbc.Col([
            create_card_with_icon(
                "Advanced Options",
                [
                    dbc.Row([
                        dbc.Col([
                            html.H5([
                                html.I(className="fas fa-toggle-on me-2"),
                                "Analysis Options"
                            ], className="mb-3"),
                            dbc.Checklist(
                                options=[
                                    {
                                        "label": "Skip Similar Frequencies",
                                        "value": "skip-similar",
                                        "title": "Ignore regions with multiple frequencies within a small range. "
                                                "Useful for avoiding over-fitting of closely spaced frequencies."
                                    },
                                    {
                                        "label": "Skip Cutoff",
                                        "value": "skip-cutoff",
                                        "title": "Override the default stopping behavior for frequency extraction. "
                                                "Continues analysis even when SNR criteria are not met."
                                    },
                                    {
                                        "label": "Do PCA",
                                        "value": "do-pca",
                                        "title": "Activate Principal Component Analysis for light curve data. "
                                                "Can help remove systematic trends and improve signal detection."
                                    },
                                    {
                                        "label": "Do PSF",
                                        "value": "do-psf",
                                        "title": "Activate Point Spread Function analysis for light curve data. "
                                                "Useful for crowded fields or contaminated apertures."
                                    },
                                    {
                                        "label": "Store Object",
                                        "value": "store-object",
                                        "title": "Save the complete SMURFS analysis object for later use. "
                                                "Enables detailed inspection and further analysis of results."
                                    },
                                    {
                                        "label": "Apply Corrections",
                                        "value": "apply-corrections",
                                        "title": "Apply automated corrections to the input files. "
                                                "Includes outlier removal and systematic trend correction."
                                    },
                                    {
                                        "label": "Improve Fit",
                                        "value": "improve-fit",
                                        "title": "Apply additional fitting improvements after the initial analysis."
                                    }
                                ],
                                id={"type": "checklist", "id": "advanced-options"},
                                switch=True,
                                className="mb-3"
                            )
                        ], width=6),
                        dbc.Col([
                            html.H5([
                                html.I(className="fas fa-wrench me-2"),
                                "Method Settings"
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Fit Method"),
                                    dcc.Dropdown(
                                        id={"type": "dropdown", "id": "fit-method"},  # Keep consistent type
                                        options=[{"label": m.name, "value": m.name}
                                                for m in FitMethod],
                                        value=FitMethod.LMFIT.name,
                                        className="mb-3"
                                    ),
                                    dbc.Tooltip(
                                        "Select the fitting method to use for frequency analysis:"
                                        "\n• LMFIT: Levenberg-Marquardt fitting (recommended)"
                                        "\n• SCIPY: SciPy's curve fitting implementation",
                                        target={"type": "dropdown", "id": "fit-method"},
                                        placement="right"
                                    )
                                ])
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Extend Frequencies"),
                                    create_input_with_validation(
                                        "extend-frequencies",
                                        "number",
                                        "Number of frequencies",
                                        min=0,
                                        value=0,
                                        help_text="Number of additional frequencies to extract beyond the default cutoff"
                                    )
                                ])
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Frequency Detection"),
                                    create_input_with_validation(
                                        "frequency-detection",
                                        "number",
                                        "Detection ratio",
                                        min=0,
                                        value=0,
                                        help_text="Minimum ratio for frequency detection"
                                    )
                                ])
                            ])
                        ], width=6)
                    ])
                ],
                "info",
                "fas fa-cogs"
            )
        ])
    ], className="mt-3")