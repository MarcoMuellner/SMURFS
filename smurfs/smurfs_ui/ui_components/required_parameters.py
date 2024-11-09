# File: smurfs/smurfs_ui/ui_components/required_parameters.py
import dash_mantine_components as dmc
from smurfs.smurfs_ui.common_ui import create_input_with_validation, create_card_with_icon


def create_required_parameters():
    return dmc.GridCol([
        create_card_with_icon(
            "Required Parameters",
            [
                dmc.Stack([
                    dmc.Stack([
                        dmc.Text("Target", fw=500),
                        create_input_with_validation(
                            "target",
                            "text",
                            "Enter star name or filename",
                            required=True,
                            help_text="Name of the target star (e.g., 'HD 24712') or path to a custom data file. "
                                      "For TESS targets, you can use the TIC ID."
                        )
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("SNR", fw=500),
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
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Window Size", fw=500),
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
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Sigma Clip", fw=500),
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
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Iterations", fw=500),
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
                    ], gap="xs")
                ], gap="md")
            ],
            "blue",
            "fas fa-asterisk"
        )
    ], span=6)