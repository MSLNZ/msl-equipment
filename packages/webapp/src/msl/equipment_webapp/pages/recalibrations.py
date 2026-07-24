"""Recalibrations page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
from __future__ import annotations

import collections
import logging

import dash
import dash_ag_grid as dag  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, dcc, html
from msl.equipment_webapp import config

from msl.equipment import Register, Status

dash.register_page(__name__, name="Recalibrations", title="MSL | Recalibrations")  # type: ignore[no-untyped-call]

log_buffer: collections.deque[str] = collections.deque()

app = dash.get_app()  # type: ignore[no-untyped-call]


class LogHandler(logging.Handler):
    """Custom handler for displaying log messages in a dash component."""

    def emit(self, record: logging.LogRecord) -> None:  # pyright: ignore[reportImplicitOverride]
        """Append the `record` to the log buffer."""
        log_entry = self.format(record)
        log_buffer.append(log_entry)


custom_handler = LogHandler()
custom_handler.setFormatter(
    logging.Formatter(fmt="%(asctime)s.%(msecs)03d [%(levelname)05s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
)
config.logger.addHandler(custom_handler)


def layout(**params: str) -> html.Div:
    """Dynamically serve the layout when the page is opened.

    Args:
        params: Query parameters in the URL, e.g., /recalibrations?team=Light&months=6
            Can specify multiple teams via `team=Light+Length`.
    """
    teams = ["MSL"] + [t.team for t in config.teams]
    team = params.get("team", "").split()
    months = int(params.get("months", 6))
    git_pull = params.get("pull", "no").lower() in {"y", "yes", "1", "true"}
    return html.Div(
        [
            dbc.Stack(
                [
                    dbc.Button("Download CSV", id="csv-button", n_clicks=0, style={"marginRight": 50}),
                    html.Div("Team(s): "),
                    dcc.Dropdown(teams, multi=True, value=team, id="team-dropdown", style={"width": "50%"}),
                    html.Div("Months: ", style={"marginLeft": 25}),
                    html.Div(dbc.Input(value=months, type="number", min=0, max=100, step=1, id="months-input")),
                    dbc.Tooltip(
                        "Number of months from today's date that a recalibration is due", target="months-input"
                    ),
                    dbc.Checklist(
                        id="git-pull-checkbox",
                        options=[{"label": "Git pull?", "value": "Pull"}],
                        value=["Yes"] if git_pull else [],
                    ),
                    dbc.Tooltip(
                        "Whether a `git pull` is performed for each register before checking",
                        target="git-pull-checkbox",
                    ),
                ],
                gap=2,
                direction="horizontal",
                style={"margin": 25, "justifyContent": "center", "display": "flex"},
            ),
            dag.AgGrid(
                id="table",
                columnDefs=[
                    {"field": name}
                    for name in ["Team", "Due Date", "ID", "Description", "Manufacturer", "Model", "Serial"]
                ],
                defaultColDef={"filter": True},
                dashGridOptions={"pagination": True, "theme": "themeAlpine"},
                columnSize="sizeToFit",
                csvExportParams={
                    "fileName": "recalibrations.csv",
                },
                getRowStyle={
                    "styleConditions": [
                        {
                            "condition": "params.rowIndex % 2 === 1",
                            "style": {"background-color": "#F3F2F1", "color": "black"},
                        },
                    ]
                },
            ),
            html.Pre(
                id="log-display",
                style={
                    "backgroundColor": "#1e1e1e",
                    "color": "#ffffff",
                    "padding": "15px",
                    "overflowY": "auto",
                    "fontFamily": "monospace",
                    "borderRadius": "5px",
                },
            ),
        ]
    )


@app.callback(  # type: ignore[untyped-decorator]
    Output("table", "exportDataAsCsv"),
    Input("csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks: int) -> bool:  # type: ignore[misc]
    """Export the data in the table as a CSV file."""
    return bool(n_clicks)


@app.callback(  # type: ignore[untyped-decorator]
    Output("months-input", "invalid"),
    Input("months-input", "value"),
)
def check_months_range(value: int | None) -> bool:  # type: ignore[misc]
    """Check if the months value is out of range."""
    return value is None


@app.callback(  # type: ignore[untyped-decorator]
    Output("table", "rowData"),
    Output("log-display", "children"),
    Input("team-dropdown", "value"),
    Input("months-input", "value"),
    Input("git-pull-checkbox", "value"),
)
def update_tables(teams: list[str], months: int | None, git_pull: list[str]) -> tuple[list[dict[str, str]], str]:  # type: ignore[misc]
    """Update the table data."""
    log_buffer.clear()

    data: list[dict[str, str]] = []
    if (not teams) or (months is None):  # months is None when value is out of [min, max] range
        return data, "\n".join(log_buffer)

    added: set[str] = set()
    select_teams = config.teams if "MSL" in teams else [t for t in config.teams if t.team in teams]
    for team in select_teams:
        if git_pull:
            team.maybe_git_pull()

        if not team.valid():
            config.logger.error("Fails schema check, skipping %s", team.url)
            continue

        # Ignore XML files in hidden directories (e.g., XML files in PyCharm's .idea directory)
        files = [file for file in team.url.rglob("*.xml") if not any(part.startswith(".") for part in file.parts)]

        config.logger.info("Checking calibration dates in %s", team.url)
        register = Register(*files)
        for equipment in register:
            if (not equipment.traceable) or (equipment.status != Status.Active):
                continue
            for report in equipment.latest_reports(date="start"):
                if (equipment.id not in added) and report.is_calibration_due(months):
                    added.add(equipment.id)  # Some equipment have multiple quantities in the same report
                    data.append(
                        {
                            "Team": register.team,
                            "Due Date": report.next_calibration_date.isoformat(),
                            "ID": equipment.id,
                            "Description": equipment.description,
                            "Manufacturer": equipment.manufacturer,
                            "Model": equipment.model,
                            "Serial": equipment.serial,
                        }
                    )

    return data, "\n".join(log_buffer)
