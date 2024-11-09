# File: smurfs/smurfs_ui/__main__.py
from dash import Dash, callback, Input, Output, State, ALL, html, _dash_renderer
import dash_mantine_components as dmc
import multiprocessing as mp
from queue import Empty
import traceback
from typing import Optional
import webbrowser
from threading import Timer

from dash.exceptions import PreventUpdate

from smurfs.smurfs_ui.ui_components.header import create_header
from smurfs.smurfs_ui.ui_components.notifications import show_success_notification
from smurfs.smurfs_ui.ui_components.required_parameters import create_required_parameters
from smurfs.smurfs_ui.ui_components.optional_parameters import create_optional_parameters
from smurfs.smurfs_ui.ui_components.advanced_options import create_advanced_options
from smurfs.smurfs_ui.ui_components.log_area import create_log_area
from smurfs.smurfs_ui.process_manager import run_analysis_process
from smurfs.smurfs_common.support.mprint import mprint, error as error_style

# Set React version for Mantine
_dash_renderer._set_react_version("18.2.0")


class SMURFSApp:
    def __init__(self):
        self.app = Dash(
            __name__,
            external_stylesheets=[
                "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
                *dmc.styles.ALL
            ],
            suppress_callback_exceptions=True
        )
        self.log_queue = mp.Queue()
        self.current_process = None
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        self.app.layout = dmc.MantineProvider(
            forceColorScheme="light",
            theme={
                "primaryColor": "indigo",
                "fontFamily": "'Inter', sans-serif",
                "components": {
                    "Button": {"defaultProps": {"fw": 400}},
                    "Alert": {"styles": {"title": {"fontWeight": 500}}},
                    "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
                    "Badge": {"styles": {"root": {"fontWeight": 500}}},
                    "Progress": {"styles": {"label": {"fontWeight": 500}}},
                    "RingProgress": {"styles": {"label": {"fontWeight": 500}}},
                    "CodeHighlightTabs": {"styles": {"file": {"padding": 12}}},
                    "Table": {
                        "defaultProps": {
                            "highlightOnHover": True,
                            "withTableBorder": True,
                            "verticalSpacing": "sm",
                            "horizontalSpacing": "md",
                        }
                    },
                },
            },
            children=[
                html.Div([
                    dmc.NotificationProvider(
                        position="top-right",
                        autoClose=3000,
                        zIndex=1000
                    ),
                    dmc.Container([
                        create_header(),
                        dmc.Grid([
                            # Left side - Input form
                            dmc.GridCol([
                                dmc.Grid([
                                    create_required_parameters(),
                                    create_optional_parameters()
                                ], gutter="md"),
                                create_advanced_options()
                            ], span=8),
                            # Right side - Log area
                            create_log_area()
                        ], gutter="xl")
                    ], size="2xl", px="md")
                ])
            ]
        )

    def setup_callbacks(self):
        @self.app.callback(
            [Output({"type": "text-input", "id": ALL}, "error"),
             Output("submit-button", "disabled")],
            [Input({"type": "text-input", "id": ALL}, "value"),
             Input({"type": "select", "id": ALL}, "value"),
             Input({"type": "switch", "id": ALL}, "checked")]
        )
        def validate_inputs_and_update_button(text_values, select_values, switch_values):
            """Validate all inputs and update button state"""
            # Initialize validation states for text/number inputs
            invalids = [None] * len(text_values)  # None means no error

            # Validate required text/number inputs
            required_indices = [0, 1, 2, 3, 4]  # Indices of required fields
            for i in required_indices:
                if i < len(text_values):  # Safety check
                    if text_values[i] is None or text_values[i] == "":
                        invalids[i] = "This field is required"
                    elif i > 0:  # Numeric validation for non-target fields
                        try:
                            val = float(text_values[i])
                            if i == 4:  # iters
                                if not float(val).is_integer() or val < 1:
                                    invalids[i] = "Must be a positive integer"
                            else:  # other numeric fields
                                if val <= 0:
                                    invalids[i] = "Must be greater than 0"
                        except (ValueError, TypeError):
                            invalids[i] = "Invalid number"

            # Check if all required fields are valid
            button_disabled = any(invalids[i] is not None for i in required_indices)

            return invalids, button_disabled

        @self.app.callback(
            Input("submit-button", "n_clicks"),
            [State({"type": "text-input", "id": ALL}, "value"),
             State({"type": "select", "id": ALL}, "value"),
             State({"type": "switch", "id": ALL}, "checked")],
            prevent_initial_call=True
        )
        def process_analysis(n_clicks, text_values, select_values, switch_values):
            if not n_clicks:
                return ""

            try:
                # Collect values from different input types
                text_fields = ["target", "snr", "window-size", "sigma-clip", "iters",
                               "freq-min", "freq-max", "extend-frequencies",
                               "frequency-detection", "save-path"]
                text_dict = dict(zip(text_fields, text_values))

                select_fields = ["mission", "flux-type", "fit-method"]
                select_dict = dict(zip(select_fields, select_values))

                # Collect switch states into advanced options list
                advanced_options = []
                switch_fields = ["skip-similar", "skip-cutoff", "do-pca", "do-psf",
                                 "store-object", "apply-corrections", "improve-fit"]
                for field, state in zip(switch_fields, switch_values or []):
                    if state:
                        advanced_options.append(field)

                switch_dict = {"advanced-options": advanced_options}

                value_dict = {**text_dict, **select_dict, **switch_dict}

                # Start analysis process
                if self.current_process and self.current_process.is_alive():
                    self.current_process.terminate()

                self.current_process = mp.Process(
                    target=run_analysis_process,
                    args=(value_dict, self.log_queue)
                )
                self.current_process.start()
                show_success_notification("Analysis started", "Check the log area for progress.")

            except Exception as e:
                tb = traceback.format_exc()
                mprint(f"Error occurred during analysis:", error_style)
                mprint(f"Error message: {str(e)}", error_style)
                mprint("Traceback:", error_style)
                for line in tb.split('\n'):
                    if line.strip():
                        mprint(f"  {line}", error_style)

                return dmc.Alert(
                    children=[
                        dmc.Text(str(e), size="sm"),
                        dmc.Space(h=10),
                        dmc.Prism(
                            tb,
                            language="python",
                            withLineNumbers=True,
                            copyLabel="Copy traceback",
                            copiedLabel="Copied!"
                        )
                    ],
                    title="Error",
                    color="red",
                    variant="filled"
                ), False  # Hide loader

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
                dmc.Text(
                    msg["text"],
                    c=msg["color"],
                    style={'padding': '2px 0'}
                ) for msg in current_messages
            ]

            return current_messages, log_entries

    def run(self, debug: bool = True, port: Optional[int] = 8050):
        Timer(1, lambda: webbrowser.open_new_tab(f'http://127.0.0.1:{port}')).start()
        self.app.run_server(debug=debug, port=port)


def main(port: Optional[int] = 8050):
    try:
        mp.set_start_method('spawn')
        app = SMURFSApp()
        app.run(port=port)
    except RuntimeError:
        pass


if __name__ == "__main__" or __name__ == "smurfs.smurfs_ui.__main__":
    main()
