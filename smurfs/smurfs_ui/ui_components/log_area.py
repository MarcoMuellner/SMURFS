# File: smurfs/smurfs_ui/ui_components/log_area.py
import dash_mantine_components as dmc
from dash import dcc, html


def create_log_area():
    return dmc.GridCol([
        dcc.Store(id='log-messages', storage_type='memory', data=[]),
        dcc.Interval(id='log-interval', interval=100),

        dmc.Paper(
            children=[
                dmc.Group([
                    html.I(className="fas fa-terminal"),
                    dmc.Title("Execution Log", order=4),
                ], gap="xs", mb="md"),
                dmc.Paper(
                    children=dmc.ScrollArea(
                        id="log-area",
                        children=[],
                        offsetScrollbars=True,
                        type="always",
                        style={
                            "height": "calc(100vh - 250px)",
                        }
                    ),
                    style={
                        "backgroundColor": "#1a1b1e",
                        "fontFamily": "monospace",
                        "fontSize": "0.875rem",
                        "padding": "10px",
                    }
                )
            ],
            p="md",
            radius="md",
            withBorder=True,
            shadow="sm",
            style={"position": "sticky", "top": "1rem"}
        )
    ], span=4)