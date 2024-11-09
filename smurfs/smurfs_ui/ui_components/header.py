import dash_mantine_components as dmc
from dash import html


def create_header():
    return dmc.Stack([
        dmc.Group(
            [
                dmc.Title(
                    dmc.Group([
                        html.I(className="fas fa-star"),
                        "SMURFS: Smart UseR Frequency analySer"
                    ], gap="xs"),
                    order=1,
                    ta="center",
                    mt="md"
                ),
                dmc.Button(
                    children=[
                        html.I(className="fas fa-play me-2"),
                        "Analyze"
                    ],
                    id="submit-button",
                    color="green",
                    size="lg",
                    radius="xl",  # Make button rounded
                    variant="filled",
                    disabled=True,
                    ml="auto",  # Push button to the far right
                    mt="auto"
                )
            ],
            style={"width": "100%", "justifyContent": "space-between"}  # Spread out items
        ),
        dmc.Text(
            dmc.Group([
                html.I(className="fas fa-chart-line"),
                "Stellar data analysis for frequency extraction"
            ], gap="xs"),
            c="dimmed",
            size="lg",
            ta="center"
        ),
        dmc.Divider(my="lg")
    ], gap="md")
