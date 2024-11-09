# File: smurfs/smurfs_ui/ui_components/optional_parameters.py
import dash_mantine_components as dmc
from smurfs.smurfs_common.preprocessing.dataloader import FluxType, Mission
from smurfs.smurfs_ui.common_ui import create_input_with_validation, create_card_with_icon


def create_optional_parameters():
    return dmc.GridCol([
        create_card_with_icon(
            "Optional Parameters",
            [
                dmc.Stack([
                    dmc.Stack([
                        dmc.Text("Frequency Range", fw=500),
                        dmc.Group([
                            create_input_with_validation(
                                "freq-min",
                                "number",
                                "Min frequency",
                                help_text="Lower bound of the frequency range to analyze (in cycles/day). "
                                          "Leave empty to start from the lowest possible frequency."
                            ),
                            create_input_with_validation(
                                "freq-max",
                                "number",
                                "Max frequency",
                                help_text="Upper bound of the frequency range to analyze (in cycles/day). "
                                          "Leave empty to analyze up to the Nyquist frequency."
                            )
                        ], grow=True)
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Mission", fw=500),
                        dmc.Select(
                            id={"type": "select", "id": "mission"},
                            data=[{"label": m.name, "value": m.name} for m in Mission],
                            value=Mission.TESS.name,
                            description="Select the space mission that provided the data. Each mission has specific data formats and characteristics.",
                            clearable=False,
                            searchable=False
                        )
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Flux Type", fw=500),
                        dmc.Select(
                            id={"type": "select", "id": "flux-type"},
                            data=[{"label": f.name, "value": f.name} for f in FluxType],
                            value=FluxType.PDCSAP.name,
                            description="Choose the type of flux measurement to analyze. PDCSAP is recommended for most cases.",
                            clearable=False,
                            searchable=False
                        )
                    ], gap="xs"),

                    dmc.Stack([
                        dmc.Text("Save Path", fw=500),
                        create_input_with_validation(
                            "save-path",
                            "text",
                            "Path to save results",
                            value=".",
                            help_text="Directory where analysis results will be saved. "
                                      "Default is the current directory ('.')"
                        )
                    ], gap="xs"),

                    dmc.Switch(
                        id={"type": "switch", "id": "improve-fit"},
                        label="Improve Fit",
                        checked=True,
                        size="md",
                        description="Apply additional fitting improvements after the initial analysis"
                    ),

                    dmc.Text(
                        "Note: Leaving optional parameters at their default values will use "
                        "optimal settings determined by the data characteristics.",
                        c="dimmed",
                        size="sm",
                        style={"fontStyle": "italic"}
                    )
                ], gap="md")
            ],
            "gray",
            "fas fa-sliders-h"
        )
    ], span=6)