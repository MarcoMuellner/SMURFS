from dash import html
import dash_bootstrap_components as dbc
from smurfs.smurfs_ui.common_ui import create_input_with_validation, create_card_with_icon

def create_required_parameters():
    return dbc.Col([
        create_card_with_icon(
            "Required Parameters",
            [
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Target"),
                        create_input_with_validation(
                            "target",
                            "text",
                            "Enter star name or filename",
                            required=True,
                            help_text="Name of the target star (e.g., 'HD 24712') or path to a custom data file. "
                                      "For TESS targets, you can use the TIC ID."
                        )
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("SNR"),
                        create_input_with_validation(
                            "snr",
                            "number",
                            "Signal to noise ratio",
                            required=True,
                            min=0,
                            help_text="Minimum signal-to-noise ratio required for frequency detection. "
                                      "Higher values result in more stringent frequency selection. "
                                      "Typical values range from 4 to 8."
                        )
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Window Size"),
                        create_input_with_validation(
                            "window-size",
                            "number",
                            "Window size for SNR",
                            required=True,
                            min=0,
                            help_text="Size of the frequency window used to calculate the local SNR. "
                                      "This defines the range around each peak where other frequencies "
                                      "are considered part of the noise. Typically 2-5 times the frequency resolution."
                        )
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Sigma Clip"),
                        create_input_with_validation(
                            "sigma-clip",
                            "number",
                            "Sigma for clipping",
                            required=True,
                            min=0,
                            value=4.0,
                            help_text="Standard deviation threshold for sigma clipping of outliers in the data. "
                                      "Points deviating more than this many standard deviations will be removed. "
                                      "Default: 4.0"
                        )
                    ], className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Iterations"),
                        create_input_with_validation(
                            "iters",
                            "number",
                            "Clipping iterations",
                            required=True,
                            min=1,
                            value=1,
                            help_text="Number of iterations for the sigma clipping procedure. "
                                      "Multiple iterations can help remove outliers more effectively. "
                                      "Default: 1"
                        )
                    ], className="mb-3")
                ])
            ],
            "primary",
            "fas fa-asterisk"
        )
    ], width=6)