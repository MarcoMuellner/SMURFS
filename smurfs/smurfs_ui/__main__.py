# File: smurfs/smurfs_ui/__main__.py
from dash import Dash, callback, Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import multiprocessing as mp
from queue import Empty
import traceback
from typing import Optional
import webbrowser
from threading import Timer

from dash.exceptions import PreventUpdate

from smurfs.smurfs_ui.common_ui import create_alert
from smurfs.smurfs_ui.ui_components.header import create_header
from smurfs.smurfs_ui.ui_components.required_parameters import create_required_parameters
from smurfs.smurfs_ui.ui_components.optional_parameters import create_optional_parameters
from smurfs.smurfs_ui.ui_components.advanced_options import create_advanced_options
from smurfs.smurfs_ui.ui_components.action_area import create_action_area
from smurfs.smurfs_ui.ui_components.log_area import create_log_area
from smurfs.smurfs_ui.process_manager import run_analysis_process
from smurfs.smurfs_common.support.mprint import mprint, error as error_style


class SMURFSApp:
    def __init__(self):
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.SUPERHERO, dbc.icons.FONT_AWESOME],
            suppress_callback_exceptions=True
        )
        self.log_queue = mp.Queue()
        self.current_process = None
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            create_header(),
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            create_required_parameters(),
                            create_optional_parameters()
                        ]),
                        create_advanced_options(),
                        *create_action_area()
                    ], width=8),
                    create_log_area()
                ])
            ], fluid=True)
        ])

    def setup_callbacks(self):
        @self.app.callback(
            [Output({"type": "text-input", "id": ALL}, "invalid"),
             Output("submit-button", "disabled")],
            [Input({"type": "text-input", "id": ALL}, "value"),
             Input({"type": "dropdown", "id": ALL}, "value"),
             Input({"type": "checklist", "id": ALL}, "value")]
        )
        def validate_inputs_and_update_button(text_values, dropdown_values, checklist_values):
            """Validate all inputs and update button state"""
            # Initialize validation states for text/number inputs
            invalids = [False] * len(text_values)

            # Validate required text/number inputs (target, snr, window_size, sigma_clip, iters)
            required_indices = [0, 1, 2, 3, 4]  # Indices of required fields in text_values
            for i in required_indices:
                if i < len(text_values):  # Safety check
                    if text_values[i] is None or text_values[i] == "":
                        invalids[i] = True
                    elif i > 0:  # Numeric validation for non-target fields
                        try:
                            val = float(text_values[i])
                            if i == 4:  # iters
                                if not float(val).is_integer() or val < 1:
                                    invalids[i] = True
                            else:  # other numeric fields
                                if val <= 0:
                                    invalids[i] = True
                        except (ValueError, TypeError):
                            invalids[i] = True

            # Check if all required fields are valid
            button_disabled = any(invalids[:5])

            return invalids, button_disabled

        @self.app.callback(
            Output("results-area", "children"),
            Input("submit-button", "n_clicks"),
            [State({"type": "text-input", "id": ALL}, "value"),
             State({"type": "dropdown", "id": ALL}, "value"),
             State({"type": "checklist", "id": ALL}, "value")],
            prevent_initial_call=True
        )
        def process_analysis(n_clicks, text_values, dropdown_values, checklist_values):
            if not n_clicks:
                return ""

            try:
                # Collect values from different input types
                text_fields = ["target", "snr", "window-size", "sigma-clip", "iters",
                               "freq-min", "freq-max", "extend-frequencies", "frequency-detection", "save-path"]
                text_dict = dict(zip(text_fields, text_values))

                dropdown_fields = ["mission", "flux-type", "improve-fit-mode", "fit-method"]
                dropdown_dict = dict(zip(dropdown_fields, dropdown_values))

                checklist_dict = {"advanced-options": checklist_values[0] if checklist_values else []}

                value_dict = {**text_dict, **dropdown_dict, **checklist_dict}

                # Start analysis process
                if self.current_process and self.current_process.is_alive():
                    self.current_process.terminate()

                self.current_process = mp.Process(
                    target=run_analysis_process,
                    args=(value_dict, self.log_queue)
                )
                self.current_process.start()

                return dbc.Alert(
                    "Analysis started. Check the log area for progress.",
                    color="info"
                )

            except Exception as e:
                # Get the full traceback
                tb = traceback.format_exc()

                # Log the error with traceback
                mprint(f"Error occurred during analysis:", error_style)
                mprint(f"Error message: {str(e)}", error_style)
                mprint("Traceback:", error_style)
                for line in tb.split('\n'):
                    if line.strip():  # Skip empty lines
                        mprint(f"  {line}", error_style)

                # Create alert with error details
                return dbc.Alert([
                    html.H4("Error", className="alert-heading"),
                    html.P(str(e)),
                    html.Hr(),
                    html.Pre(
                        tb,
                        style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'fontSize': '0.8rem',
                            'backgroundColor': 'rgba(0,0,0,0.1)',
                            'padding': '10px',
                            'borderRadius': '4px'
                        }
                    )
                ], color="danger")

        @self.app.callback(
            [Output('log-messages', 'data'),
             Output('log-area', 'children')],
            Input('log-interval', 'n_intervals'),
            State('log-messages', 'data'),
            prevent_initial_call=True
        )
        def update_logs(n_intervals, current_messages):
            if current_messages is None:
                current_messages = []

            try:
                while True:  # Process all available messages
                    msg = self.log_queue.get_nowait()
                    current_messages.append(msg)
            except Empty:
                pass

            if not current_messages:
                raise PreventUpdate

            # Create log entries
            log_entries = [
                html.Div(
                    msg["text"],
                    style={'color': msg["color"], 'padding': '2px 0'}
                ) for msg in current_messages
            ]

            return current_messages, log_entries

    def run(self, debug: bool = True, port: Optional[int] = 8050):
        Timer(1, lambda: webbrowser.open_new_tab(f'http://127.0.0.1:{port}')).start()
        self.app.run_server(debug=debug, port=port)


def open_browser():
    webbrowser.open_new_tab('http://127.0.0.1:8050')


def main(port: Optional[int] = 8050):
    mp.set_start_method('spawn')
    app = SMURFSApp()
    app.run(port=port)


if __name__ == "__main__" or __name__ == "smurfs.smurfs_ui.__main__":
    main()