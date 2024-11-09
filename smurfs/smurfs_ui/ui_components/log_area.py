# File: smurfs/smurfs_ui/ui_components/log_area.py
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_log_area():
    return dbc.Col([
        dcc.Store(id='log-messages', storage_type='memory', data=[]),
        dcc.Interval(id='log-interval', interval=100),

        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="fas fa-terminal me-2"),
                    "Execution Log"
                ], className="mb-0")
            ], className="bg-dark text-white"),
            dbc.CardBody([
                html.Div(
                    id="log-area",
                    className="font-monospace",
                    style={
                        'height': 'calc(100vh - 200px)',
                        'overflowY': 'auto',
                        'whiteSpace': 'pre-wrap',
                        'backgroundColor': '#1a1a1a',
                        'color': '#ffffff',
                        'padding': '10px',
                        'fontFamily': 'monospace',
                        'fontSize': '0.875rem',
                    }
                )
            ], style={'padding': '0'})
        ], className="sticky-top")
    ], width=4)