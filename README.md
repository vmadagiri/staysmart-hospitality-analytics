# StaySmart 🏨
### Explore smarter. Stay better.

**A travel discovery and personalization project built with real Washington, D.C. accommodation data.**

I wanted to build something that went beyond a typical data dashboard. Instead of just showing charts and statistics, I wanted people to actually use the data to make a decision.

That's how **StaySmart** came together: an interactive website where travelers can explore accommodations, narrow down their options, compare properties, and see why certain stays might be a better match.

Built by **Vaishnavi Madagiri** | M.S. Data Science, Virginia Tech

**[🌐 Try StaySmart](https://staysmart-vm.streamlit.app/)** | **[💻 Explore the Code](https://github.com/vmadagiri/staysmart-hospitality-analytics)**

---

## The Idea

Finding a place to stay sounds simple until you start comparing dozens of listings.

One property is cheaper, another has better reviews, and a third has everything you need but is in a different neighborhood.

I wanted to see if I could make that process easier using data.

My goal was to build a tool that answers three questions:

1. Which accommodations actually meet my requirements?
2. Which ones match my personal preferences?
3. Why is one stay recommended over another?

I started with a real dataset and gradually developed it into an interactive travel discovery experience.

## What's Inside StaySmart?

### 🔎 Discover Stays
Search real accommodation listings using filters for budget, guest count, bedrooms, neighborhood, property type, review scores, and amenities.

I included sorting and pagination so users don't have to scroll through thousands of properties at once.

### 💜 Personalized Picks
This is the feature I was most interested in building.

Users can set their requirements and preferences, and StaySmart returns up to five ranked recommendations.

Instead of displaying a match score without context, the app explains how each property fits the user's choices.

### ⚖️ Compare Stays
Sometimes two properties look equally good until you compare them side by side.

I added an option to compare up to three stays based on price, guest capacity, bedrooms, reviews, and reported amenities. Personalized comparisons also show match scores.

### 📊 Market Insights
I wanted the project to be useful for exploring the data itself, too.

The analytics page includes interactive Plotly charts covering nightly prices, neighborhood trends, property types, review scores, amenities, and an approximate location map.

### 🗂️ Behind the Data
This section explains where the information comes from, how it was cleaned, what the findings mean, and where the data has limitations.

I wanted users to understand what they're looking at rather than assume every number tells the full story.

---

## Starting With Real Data

I used the **Inside Airbnb Washington, D.C. dataset**, dated September 19, 2026.

I chose it because it includes actual public accommodation listings, prices, property details, reviews, amenities, and location information.

### A few things I found

| Metric | Result |
|---|---:|
| Total listings analyzed | 6,906 |
| Listings with valid prices | 5,993 |
| Median reported nightly price | $213.50 |
| Entire homes or apartments | 76.2% |
| Average reported review score | 4.76 / 5 |

One thing I had to account for was missing information. For example, **913 listings didn't have valid reported prices**.

Rather than making up prices or removing those listings completely, the cleaning pipeline preserves them for analyses that don't require price information. They're excluded when someone searches using a maximum budget.

That distinction matters because missing data shouldn't automatically mean the entire record is useless.

## How I Built It

I kept the technical stack straightforward because I wanted the data processing, recommendation logic, and interface to be easy to understand and test.

| Technology | What it's used for |
|---|---|
| Python | Main application logic |
| pandas | Data cleaning, filtering, and analysis |
| Streamlit | Interactive website and user controls |
| Plotly | Charts and geographic visualizations |
| CSV / JSON | Processed data and cleaning audit |
| unittest | Automated checks for key functionality |
| GitHub | Version control and source hosting |
| Streamlit Community Cloud | Public deployment |

### The Data Pipeline

```text
Inside Airbnb (CSV.gz)
        ↓
Download and validate
        ↓
Clean with Python + pandas
        ↓
Save processed data + audit
        ↓
Apply search filters and recommendation scores
        ↓
Display results in Streamlit + Plotly
```

I separated the project into smaller Python modules rather than putting everything into one large file.

| File | Responsibility |
|---|---|
| `app.py` | Website layout, navigation, and interactive features |
| `src/clean_data.py` | Downloading, validating, and cleaning listings |
| `src/recommend.py` | Filtering and recommendation scoring |
| `src/analytics.py` | Market statistics and summary calculations |
| `tests/` | Automated testing |
| `assets/` | Original logo, illustrations, and styling |
| `docs/` | Data audit, project walkthrough, and technical notes |

## How the Recommendations Work

StaySmart uses a **rule-based recommendation system**, not a trained machine-learning model.

I wanted the recommendations to be transparent so users could understand why a property appeared in their results.

The process has two steps.

**Step 1: Filter out stays that don't meet the requirements.**

For example, if someone sets a $200 maximum budget and needs room for two guests, properties that exceed the price limit or can't accommodate two people are excluded.

**Step 2: Score the remaining stays.**

The algorithm uses five weighted factors:

| Factor | Base weight |
|---|---:|
| Budget fit | 30% |
| Review score | 30% |
| Preferred amenities | 20% |
| Preferred neighborhood | 10% |
| Capacity fit | 10% |

Each factor is normalized between 0 and 1 before the weighted score is calculated.

If users don't select certain optional preferences, those weights are removed and the remaining weights are rescaled.

The results are then ranked from highest to lowest, with lower price and listing ID used to break ties.

**Important:** These are initial design weights, not weights learned from actual customer behavior. A 93/100 match score doesn't mean there's a 93% chance someone will book.

## What Changed Along the Way?

StaySmart didn't start out looking like the current website.

The first working version focused on getting the data, filters, recommendations, and analytics in place. Once I started testing it locally, I realized that having the right information wasn't enough. It also needed to be easy to navigate and understand.

A few improvements came out of that process:

- **Clearer recommendations:** Made match scores more visible and added explanations and score breakdowns.
- **Better comparisons:** Added a side-by-side view for up to three stays.
- **Improved design:** Introduced a StaySmart logo, original D.C.-inspired illustrations, and a consistent navy, ivory, and lavender style.
- **Cleaner navigation:** Made the four sections easier to move between and reduced unnecessary scrolling.
- **Bug fixes:** Addressed a Streamlit pagination/session-state warning and an undefined map title.
- **More testing:** Added regression tests to check that fixes didn't break existing behavior.

I used AI coding assistance during development, especially for implementation, debugging, styling, and documentation. I guided the requirements, reviewed the local interface, reported issues, and requested changes while working through how the application functions.

This was also a useful reminder that **a working feature and a good user experience aren't always the same thing**.

## Testing and Validation

The project has **18 automated tests** covering areas such as:

- Data cleaning, missing values, and schema validation
- Essential filters and recommendation calculations
- Score normalization and ranking behavior
- Navigation, pagination, and filter resets
- Property comparisons and empty results
- Map title and configuration

I also tested the interface locally and deployed the application through Streamlit Community Cloud.

Automated tests help verify expected behavior, but they don't replace real user testing or guarantee that every browser and device will behave the same way.

## What I Would Improve Next

There are several directions I'd like to explore as I continue learning.

**1. Test the recommendations with real users.**

The current scoring weights are based on design choices. I'd like to test whether people find the recommended stays useful and adjust the ranking based on feedback.

**2. Explore machine learning.**

With appropriate user interaction data, I could compare the current rule-based approach with a learned ranking model.

**3. Add live travel information.**

Right now, StaySmart uses a historical dataset. A production version would need current pricing, fees, trip dates, and actual availability.

**4. Improve performance at scale.**

For much larger datasets, I'd explore database-backed filtering, scheduled data updates, and more efficient loading.

## Run It Locally

Use Python 3.12.

```bash
git clone https://github.com/vmadagiri/staysmart-hospitality-analytics.git
cd staysmart-hospitality-analytics

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
python -m src.clean_data
python -m streamlit run app.py
```

To run the automated tests:

```bash
python -m unittest discover -s tests -v
```

The app downloads the official source data when needed. Raw and processed datasets aren't included in this repository.

## Data Source and Limitations

Data: [Inside Airbnb — Washington, D.C.](https://insideairbnb.com/get-the-data/)  
Snapshot: September 19, 2026; actual scrape dates September 19–20, 2026  
License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

This is an independent portfolio project and isn't affiliated with Marriott or Airbnb.

StaySmart uses historical public listings, not live booking inventory. Prices may not include fees, and availability fields cannot reliably tell us whether a property was booked or blocked by its host. Location coordinates are approximate.

The project doesn't claim to measure bookings, occupancy, revenue, or improvements in conversion.

## Why This Project Matters to Me

What I enjoyed most about StaySmart was connecting data analysis to an actual user experience.

I wanted to go beyond cleaning a dataset and creating visualizations. I wanted to understand how the same data could help someone make a choice, and how to make that choice easier to explain.

It's the kind of work I'm interested in exploring further: **data engineering, analytics, personalization, and building technology around real user needs.**

---

**Built by Vaishnavi Madagiri**

[Live StaySmart Website](https://staysmart-vm.streamlit.app/) · [GitHub Profile](https://github.com/vmadagiri) · [Project Walkthrough](docs/PROJECT_WALKTHROUGH.md)
