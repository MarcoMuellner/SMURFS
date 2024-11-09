from dash import html
import dash_bootstrap_components as dbc

def create_action_area():
    return [
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-play me-2"),
                    "Analyze"
                ],
                    id="submit-button",
                    color="success",
                    size="lg",
                    className="mt-3 w-100",
                    disabled=True
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Spinner(
                    html.Div(id="results-area", className="mt-4"),
                    color="primary",
                    type="border",
                    size="lg"
                )
            ])
        ])
    ]