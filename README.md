# StaySmart
### Explore smarter. Stay better.

Washington, D.C. accommodation discovery and explainable personalization.
Built by **Vaishnavi Madagiri** · [GitHub](https://github.com/vmadagiri)

**Status:** implemented and tested locally using Streamlit AppTest. Not publicly deployed. Desktop/mobile visual checks and app screenshots remain pending because the available browsers could not reach the development server.

## Problem
Finding a suitable stay means balancing price, location, space, and amenities. StaySmart turns public listings into a searchable experience and explains why each recommended stay fits a visitor's preferences.

## Features
- Discover Stays: price, neighborhood, property type, guest count, bedrooms, review score, and amenity filters; sorting and pagination.
- Personalized Picks: five matches with individual explanations and component scores.
- Market Insights: filtered metrics, price distributions, neighborhood comparisons, amenities, property types, reviews, summary availability, and an approximate location map.
- Behind the Data: cleaning audit, verified findings, attribution, and limitations.

## Data and attribution
Source: [Inside Airbnb](https://insideairbnb.com/get-the-data/), Washington, D.C., United States. Snapshot dated **September 19, 2026**, the latest listed at retrieval. Actual scrape dates: September 19–20, 2026.

[Original detailed listings.csv.gz](https://data.insideairbnb.com/united-states/dc/washington-dc/2026-09-19/data/listings.csv.gz)

Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). StaySmart selects fields, cleans values, aggregates statistics, and adds preference scores. No endorsement is implied.

Original download SHA-256: `4ec55977ada4b55d1a2d3641f6d49cc321dc82d3c895fe4bf22dc19fa8fecdf8`.

Inside Airbnb asks users not to republish data files. Raw and processed CSVs are Git-ignored. The app downloads the pinned official file once when needed, stores it locally, and caches reads. A cold deployment requires source availability; the source may eventually archive the snapshot. An unavailable source produces an error message instead of substitute data. Listing photographs are omitted because the dataset license does not establish rights to third-party photos. Cards use typography and amenity tags instead.

## Verified findings
Calculated from the full cleaned snapshot:
- 6,906 records before and after cleaning; no duplicate or missing listing IDs removed.
- 5,993 listings have valid prices; 913 have missing prices. Median reported nightly listing price: **$213.50**.
- 5,260 listings (**76.2%**) are entire homes or apartments.
- 5,565 listings have reported review scores; their listing-weighted average is **4.76/5**.

These are listing statistics, not booking outcomes. See `docs/data_audit.json` for the recorded schema and audit.

## Tools and structure
Python 3.12, pandas, Streamlit, Plotly, compressed CSV, and Python standard-library tests. No database, paid API, chatbot, or machine-learning model.

| File | Purpose |
|---|---|
| `app.py` | Four interactive pages |
| `src/clean_data.py` | Download, validate columns, clean, and audit |
| `src/recommend.py` | Essential filters and explainable ranking |
| `src/analytics.py` | Shared summary calculations |
| `data/raw/` | Original download, kept locally |
| `data/processed/` | Allowlisted property fields and cleaning audit |
| `tests/test_project.py` | Cleaning, scoring, metrics, and app checks |
| `.streamlit/config.toml` | Warm white, navy, and lavender theme |

## Run locally
Use Python 3.12. Open a terminal inside this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.clean_data
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. `requirements.txt` pins direct dependencies; `requirements-lock.txt` is preserved from the original project. The current checks used Python 3.12 and the three pinned direct dependencies in `requirements.txt`; the old full lock file was not revalidated. Use `requirements.txt` for setup.

## Cleaning decisions
Retain records unless the listing ID is absent or duplicated. Parse dollar signs and commas from prices; nonpositive or invalid values become missing. Do not infer missing prices, bedrooms, capacity, reviews, or amenities. Unknown prices remain available for non-price analysis. Search requires reported price, capacity, and bedrooms. Zero bedrooms can represent a studio.

Review scores outside 0–5, or scores with no reviews, become missing. Invalid availability counts become missing. A broad D.C. coordinate extent is a sanity check, not an exact boundary test. Unknown amenities cannot satisfy a must-have. Parking includes paid/free and street parking. High prices stay in the data; optional 99th-percentile trimming affects price charts only. Metrics retain the full filtered population.

Only property fields are retained in processed data. Host identities, review text, and estimated occupancy/revenue fields are excluded.

## Recommendation method
First enforce maximum price, minimum capacity, bedrooms, review threshold, property type, and required amenities. Then rank eligible listings:

| Component | Normalized value | Base weight |
|---|---|---|
| Budget fit | `1 - price / budget` | 30% |
| Review score | `review_score / 5`; unknown earns zero | 30% |
| Amenity match | Share of nice-to-haves reported | 20% |
| Neighborhood match | 1 for preferred area, otherwise 0 | 10% |
| Capacity fit | `guests / accommodates` | 10% |

Components are bounded between 0 and 1. Remove unspecified amenity/neighborhood preferences and rescale active weights to total 100%. Multiply the weighted average by 100. Ties use lower price, then listing ID. These weights are design choices, not learned from customer behavior. The score is not a probability or guarantee. Giving unknown reviews zero points may disadvantage new listings.

## Limitations
This historical Airbnb snapshot is not Marriott inventory. Prices are not live quotes, and may exclude fees or reflect different stay conditions. Trip dates and minimum-stay eligibility are not checked. Locations are approximate; map background tiles require internet access and have a plain-background fallback.

Availability charts use overlapping 30/60/90/365-day summary fields in detailed listings. No separate calendar file was downloaded. Unavailable nights can reflect bookings or host blocks. No bookings, revenue, occupancy, cancellations, conversions, or customer identities are inferred.

With authorized customer behavior and booking data, future work could evaluate ranking relevance, search completion, and A/B tests. This project does not establish a business uplift.

## Validation and screenshots
Fourteen automated checks passed, including all four pages, empty searches, score normalization and independent score calculation, required filters, missing values, duplicates, schema errors, offline download failure, and metric reconciliation. Tests deliberately alter copies of real rows to check invalid inputs; these fixtures are never used in the app.

Browser layout testing and app screenshots are **not yet verified**. After launching locally, capture Discover Stays and Market Insights at desktop width and check the same pages at 390px mobile width. Save actual captures in `docs/screenshots/`; do not use mock screenshots. OpenStreetMap tile rendering also needs this browser check.

## Deploy to Streamlit Community Cloud
No GitHub changes or deployment were performed during this update. Confirm your repository and permissions before following these optional steps.

After approval:
1. Push the reviewed source to the repository's `main` branch. Keep data files and secrets excluded.
2. Make the repository public if desired for recruiter review.
3. Sign in at https://share.streamlit.io/ using GitHub and authorize access to this repository.
4. Choose **Create app**, repository `vmadagiri/staysmart-hospitality-analytics`, branch `main`, main file `app.py`.
5. In advanced settings select Python **3.12**. No secrets are needed.
6. Request subdomain `staysmart-vm` if available, then deploy.
7. Set the app's sharing to public. Open the returned URL in an incognito window and confirm visitors need no login. Test all four pages, filters, empty results, charts, map, and mobile layout.
8. Add the verified live URL here only after those checks succeed.

[Official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

**Live website:** pending deployment; `staysmart-vm.streamlit.app` is a requested address, not a verified live site.

## 60-second interview explanation
I built StaySmart to explore how data can make travel discovery easier. I used real public accommodation listings from Washington, D.C., cleaned them with pandas, and built an interactive Streamlit app. Visitors can filter stays by budget, location, space, and amenities. The app then ranks eligible listings using a simple scoring method and explains each recommendation.

I also built a dashboard to explore prices, reviews, and listing availability. One important decision was keeping missing prices out of price-based searches without throwing away those listings from the rest of the analysis. I was careful to distinguish listed prices and availability from actual bookings or revenue.

This connects to my interest in Marriott's digital personalization and optimization work: using data to make choices more relevant and easier to understand. With real customer behavior data, my next step would be testing whether the recommendations help users complete their searches.


## November 2026 interface update
- Active-page button navigation and a compact, page-specific header.
- Ivory, navy, and lavender styling in `assets/style.css`; no external font or photo assets.
- Discover's extra filters are collapsible. Recommendations keep preference controls visible.
- Listing cards show readable prices, amenity tags, direct original-listing links, and expanded details.
- Recommendation bars show actual component values, effective weights, and points. Missing reviews remain explicit.
- Market Insights includes neighborhood listing counts, a shorter price comparison, and richer map hover details. The box plot shows up to 12 neighborhoods; the full table retains all areas.
- Behind the Data includes a responsive five-step pipeline diagram.
- The raw data, processed data, audit files, cleaning, analytics, and recommendation modules are unchanged.

## Read and practice
- [Project walkthrough](docs/PROJECT_WALKTHROUGH.md)
- [Marriott interview preparation](docs/MARRIOTT_INTERVIEW_PREP.md)
- [Validation and remaining checks](docs/VALIDATION.md)

Extract the updated folder separately from your existing project. The download excludes the machine-specific virtual environment and Git metadata. Create a new virtual environment with the commands above; retain your original project folder.

## Interactive design update
Original SVG logo/favicon, compact lavender hero, labeled illustration cards, four-amenity previews, reset controls, and comparison of up to three currently eligible stays. Changing filters or sorting restarts pagination. Personalized comparisons include the actual match score. Python, pandas, Streamlit, and Plotly remain the only main tools; no new dependencies.

Run from this folder using Python 3.12 (the tested version):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Run checks with `python -m unittest discover -s tests -v`.

## Latest refinement
Fixed the `discover_page` duplicate-default warning. Session state owns pagination initialization; search changes and reset return to page 1. Added an original SVG skyline hero, refreshed doorway/pin logo, higher-contrast cards, review badges, large match-score panels, and framed charts. All 17 automated tests pass. Browser appearance still needs local visual review.
