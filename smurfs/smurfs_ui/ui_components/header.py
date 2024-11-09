from dash import html
import dash_bootstrap_components as dbc

def create_header():
    return dbc.Container([
        html.H1([
            html.I(className="fas fa-star me-2"),
            "SMURFS: Smart UseR Frequency analySer"
        ], className="text-center my-4"),
        html.P([
            html.I(className="fas fa-chart-line me-2"),
            "Stellar data analysis for frequency extraction"
        ], className="text-center text-muted mb-4"),
        html.Hr()
    ])