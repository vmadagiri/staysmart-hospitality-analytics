# Current validation

17 unittest/AppTest tests passed on Python 3.12. Coverage includes navigation, filters, comparison, score breakdowns, unknown data, empty results, pagination, reset, and returning to Discover after navigating away.

The pagination regression test confirms `value=None`, verifies session-state initialization and reset, and checks no Session State API warning is rendered. Other widget defaults were inspected. The warning was fixed rather than disabled.

The raw/processed datasets, audit, and all three core modules are byte-identical to the previous Interactive ZIP. No dependencies changed. SVG and CSS assets are local. No GitHub push or deployment.

Desktop/mobile visual rendering and map tiles have not been verified in a browser for this revision. Automated widget checks do not establish visual appearance. External listing availability was not rechecked.

Changed: app.py, assets/style.css, assets/logo.svg, tests/test_interface.py, README.md, docs/PROJECT_WALKTHROUGH.md, docs/MARRIOTT_INTERVIEW_PREP.md, docs/VALIDATION.md.
Added: assets/travel.svg.

## Map heading correction
18 tests now pass. The map previously omitted title text while draw_chart applied title styling. The map now explicitly sets “Washington, D.C. listing locations”; the separate section heading was removed. AppTest verifies the serialized Plotly title contains this text, not undefined, and preserves scattermap coordinates, hover fields, and OpenStreetMap style. Browser pixels were not independently verified. Only app.py, the map regression test, and this validation note changed.
