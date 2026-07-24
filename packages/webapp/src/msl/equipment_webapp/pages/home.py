"""Home page."""

from __future__ import annotations

import dash
from dash import dcc

dash.register_page(__name__, path="/", name="Home", title="MSL | Home")  # type: ignore[no-untyped-call]  # pyright: ignore[reportUnknownMemberType]

body = """
__There are various pages available to help manage your equipment register.__

### [/recalibrations](/recalibrations)

<details>
  <summary>Click here to expand the dropdown</summary>

Check when equipment needs to be recalibrated. Select the team(s) and specify the number of
months in the future to check if a recalibration is due.

You can also pre-populate the fields in the URL, this allows you to bookmark a URL with custom settings.

Specify a `team`
  - <dccLink href="/recalibrations?team=Light" />

Specify a `team` and the `months` parameter (each `name=value` pair is separated by the `&` symbol)
  - <dccLink href="/recalibrations?team=Light&months=12" />

Specify the `pull` parameter (a `true` value can be one of `1`, `y`, `yes` or `true`)
  - <dccLink href="/recalibrations?pull=yes" />

Specify multiple `team`s by separating each value with the `+` sign
  - <dccLink href="/recalibrations?team=Light+Length" />

</details>

"""

layout = dcc.Markdown(body, dangerously_allow_html=True, style={"margin": 25})
