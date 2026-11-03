# StaySmart project walkthrough

## 1. Business problem
Travelers need to compare budget, location, space, and amenities. StaySmart makes these priorities explicit and shows the reasons behind a shortlist. It is a portfolio prototype; improved conversion or customer satisfaction has not been measured.

## 2. Dataset choice
Inside Airbnb provides real public Washington, D.C. accommodation listings with prices, amenities, capacity, reviews, and approximate coordinates. The pinned snapshot is September 19, 2026; records were scraped September 19–20. This is Airbnb inventory, not Marriott inventory. Source and CC BY 4.0 links are in the README and app footer.

## 3. Download
`src/clean_data.py` defines `SOURCE_URL`, `SNAPSHOT`, and the allowlisted `COLUMNS`. `build_data()` downloads detailed `listings.csv.gz` only if the local raw file is absent. It writes to a temporary download path before moving the completed file. Then it calls:

```python
raw = pd.read_csv(raw_path, low_memory=False)
cleaned, audit = clean_listings(raw)
```

The original remains in `data/raw/`. The processed CSV and audit are stored in `data/processed/`. A SHA-256 checksum identifies the raw file; it records provenance but is not an automatic integrity comparison against a fixed expected hash. Git ignores both data directories except their placeholders.

## 4. Cleaning
`clean_listings()` checks the required columns before selecting them. It converts listing IDs to nullable integers, uses `dropna(subset=['id'])`, then `drop_duplicates(subset=['id'], keep='first')`. It renames neighborhood and rating fields, parses numeric columns, and sorts by ID. The current snapshot retains all 6,906 rows; zero missing or duplicate IDs were removed.

`parse_amenities()` parses JSON strings. It distinguishes unknown amenity data from a known empty list through `amenities_known`. Wi-Fi, kitchen, and parking flags support filters; parking can include paid, free, or street parking. This is a simple text rule, not a complete amenity taxonomy.

## 5. Missing and invalid values
Dollar signs and commas are removed before `pd.to_numeric(..., errors='coerce')`. Nonpositive prices become missing. The snapshot has 913 missing prices and 5,993 valid prices. No price is imputed. Unknown prices remain useful for non-price analysis but cannot pass a price-based search.

Scores outside 0–5, or scores on records with no reviews, become missing. Negative bedrooms and capacities below one become missing. Zero bedrooms is retained for studios. Availability must fall between zero and its window size. Coordinates outside a broad D.C. bounding box are excluded from the map without deleting the listing. This box is not an exact district polygon.

## 6. Filters
`filter_listings()` in `src/recommend.py` uses Boolean masks:

```python
matches = data.loc[data.price.notna() & data.price.le(budget)
                   & data.accommodates.ge(guests)
                   & data.bedrooms.ge(bedrooms)].copy()
```

Neighborhood and property choices use `isin()`. A positive review minimum excludes unknown reviews. Each required amenity must have a true flag. Discover treats selected neighborhoods as requirements; Personalized Picks treats preferred neighborhoods as ranking preferences. No selection means no restriction for those categories.

## 7. Recommendation algorithm
`recommend()` calls the essential filters first. It then calculates five values between zero and one:

| Component | Calculation | Base weight |
|---|---|---|
| Budget | `1 - price / budget`, clipped to 0–1 | .30 |
| Review | `review_score / 5`, unknown set to 0 | .30 |
| Amenities | Fraction of preferred amenity flags that are true | .20 |
| Neighborhood | 1 if preferred, otherwise 0 | .10 |
| Capacity | `guests / accommodates`, clipped to 0–1 | .10 |

The exact score is `100 * sum(component * weight) / sum(active_weights)`. Unselected amenity and neighborhood preferences are removed. With neither selected, active weights total .70; the remaining effective weights are 42.86%, 42.86%, and 14.29%. With all components selected, the denominator is 1.

Lower prices get more budget points; the score does not reward spending the full budget. Capacity rewards a closer size fit among stays that already accommodate the party. Reviews are not weighted by review count. Unknown reviews earn zero points, which can disadvantage new listings. Weights are design choices and have not been calibrated against outcomes.

`sort_values(['match_score', 'price', 'id'], ascending=[False, True, True]).head(5)` selects the results. `explain_match()` generates reasons from those same listing fields. The redesigned card displays normalized bars, effective weights, and point contributions; display rounding does not alter ranking.

## 8. Dashboard calculations
`metrics()` in `src/analytics.py` counts filtered records and reported prices, takes the median of valid prices, and computes the unweighted mean of reported listing review scores. `neighborhood_prices()` uses `groupby('neighborhood')` to calculate price counts and medians. `common_amenities()` deduplicates amenities within each listing before exploding and counting them.

The dashboard also counts neighborhoods and property types with `value_counts()`. Price charts optionally hide values above the filtered 99th percentile. The neighborhood box plot then shows up to 12 neighborhoods with the most displayed listings, while the summary table retains every neighborhood. This changes only the two price charts, not KPI calculations. Availability is the mean reported available days divided by the window size, multiplied by 100; windows overlap. The map uses valid coordinates and optional OpenStreetMap tiles.

## 9. Streamlit integration
`app.py` connects the modules. `load_data()` is cached with `st.cache_data`; it reads processed files or calls `build_data()` when needed. Streamlit reruns the page after widget changes. Native navigation buttons select one of four page branches. `search_controls()`, `listing_card()`, and `draw_chart()` keep repeated interface behavior together.

Cards use escaped listing text when building HTML. They display no property photographs. Theme colors come from `.streamlit/config.toml`; `assets/style.css` supplies editorial headings, compact navigation, restrained borders, price hierarchy, and amenity tags. Mobile CSS reduces heading sizes and stacks the wordmark subtitle. Actual mobile rendering still needs browser verification.

## 10. Tests
`tests/test_project.py` uses unittest and Streamlit AppTest. It checks real-source counts, schema errors, duplicate IDs, dirty numeric fields, invalid coordinates, amenity parsing, essential filters, independent score calculation, determinism, inactive preference normalization, empty results, CSV round trips, offline download failure, dashboard metrics, and all four page branches. Deliberately altered copies of source rows are test fixtures only.

Run `python -m unittest discover -s tests -v`. AppTest executes widgets and Python rendering but does not prove browser appearance or external map tile availability.

## 11. Tradeoffs
Simple pandas rules make the project explainable and easy to inspect. They do not learn from clicks or bookings. Unknown prices are retained for analytical completeness. Source data files are not republished in Git, so cold startup depends on the official download remaining available. Photos are omitted because reusability is not established. A small, transparent feature set is easier to discuss than an unvalidated complex model.

## 12. Limits and next steps
Listing prices are historical asking prices, not revenue or live quotes. Unavailable dates do not establish bookings or occupancy. Minimum-stay information is displayed but trip-date eligibility is not evaluated. No customer history is collected. Next steps could include usability interviews, sensitivity analysis of weights, review-count-aware ranking, and—only with authorized behavioral data—offline ranking evaluation and controlled experiments. None of these improvements or business outcomes has been claimed as completed.


## Worked scoring example from a real result
The example below comes from the uploaded processed snapshot, using a $250 budget, two guests, zero minimum bedrooms, and no optional preferences. It is an illustration of the existing algorithm, not an invented property.

Listing ID `29082182` has a snapshot price of $37.90, a review score of 5.00/5, and capacity for 2 guests.

`100 × (0.30 × 0.848400 + 0.30 × 1.000000 + 0.10 × 1.000000) / 0.70 ≈ 93.50`.

The code uses full precision; this example rounds the components. The interface rounds the final score to one decimal. Nice-to-have amenities and neighborhoods are absent, so their weights do not enter the denominator.

The final validation run passed 17 tests. Three additional interface checks reconcile displayed points, exercise unknown-price analytics, and check navigation and listing-link structure. See `docs/VALIDATION.md` for what was and was not verified.

## Interface update: branding and comparison
`assets/logo.svg` is an original location pin containing a small hotel symbol. `app.py` reads it into the wordmark and passes its path to `st.set_page_config(page_icon=...)`. All CSS remains in `assets/style.css`. Cards use a clearly labeled generic building illustration, not property photography. Four amenities appear initially; the expander shows the complete reported list and full title.

`search_controls()` uses normal Streamlit widgets, not a form. Each committed change reruns the script and passes current values to `filter_listings()` or `recommend()`. Number inputs update when committed (Enter, focus change, or step buttons). `reset_filters()` clears that page's widget keys in a callback. Changing search results or sorting resets the results page to one.

`compare_stays()` uses a multiselect and ordinary columns:

```python
selected = st.multiselect('Choose stays', lookup.index.tolist(), key=key, max_selections=3,
                          format_func=lambda item: f"{lookup.loc[item, 'name']} · ${lookup.loc[item, 'price']:,.2f} · #{item}")
```

Discover comparison choices come from all current results, not only the visible page. Personalized Picks comparison choices come from the current top five. Selections that leave those results are removed. Comparison shows historical price, review score, neighborhood, property type, capacity, bedrooms, amenity flags, and (for recommendations) the actual current match score. A missing amenity is described as not reported, not definitely absent. Comparison is session-only and does not save bookings or customer profiles.

`draw_chart()` applies a shared Plotly theme. Counts use `value_counts()`, price comparisons use actual filtered prices, and review histograms omit missing scores. Hover labels expose the chart's underlying values. Maps use valid source coordinates; no invented locations are added. No scoring, cleaning, data, or dependency changes were needed.

## Pagination warning fix and visual refinement
`discover_page` previously had both `value=1` and a session-state assignment. It now uses `value=None`, so session state is the single source of initialization. The state is set to 1 when a search changes or the key is absent, including after leaving and returning to Discover. Reset still starts at page 1. An intentionally cleared page input displays a prompt until a page is entered. Other widget defaults were checked; comparison uses no explicit default and filter reset deletes keys rather than assigning competing values.

The navy hero uses `assets/travel.svg`, an original stylized D.C. skyline and travel route. It is an illustration, not a geographic map or listing image. `assets/logo.svg` now combines a pin and arched doorway. Cards have CSS building illustrations, serif titles, larger prices, lavender review badges, and navy listing buttons. Personalized Picks uses large navy score panels and checkmarked explanations from the existing `row.reasons`. `draw_chart()` gives charts a bordered container, white plotting area, and larger titles. All presentation rules remain in one CSS file; no dependency or scoring changes.
