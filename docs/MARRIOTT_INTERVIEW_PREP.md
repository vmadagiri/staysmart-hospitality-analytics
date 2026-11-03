# StaySmart interview preparation

Use these as practice answers. Confirm that each first-person action accurately describes your contribution, including where coding assistance was used. Do not claim measured business results.

## 30-second pitch
I built StaySmart to explore how data can make travel discovery easier. It uses real Washington, D.C. accommodation listings and lets visitors filter by budget, space, location, and amenities. A simple scoring system then recommends five stays and explains why they match. I used pandas, Streamlit, and Plotly so the project stays easy to understand and test.

## 60-second pitch
I built StaySmart around a simple travel problem: people have different priorities, but a long list of properties does not always help them decide. I used real public accommodation listings from Washington, D.C., cleaned them with pandas, and created a Streamlit app with search, recommendations, and market insights.

I separate must-haves from preferences. A listing has to meet the budget, capacity, and other requirements before it can be ranked. Then I score budget fit, reviews, amenities, neighborhood, and capacity. Each recommendation shows its reasons and the actual score breakdown.

I also kept the limitations visible. Missing prices are not guessed, and unavailable dates are not treated as bookings. This connects to my interest in digital personalization: making choices more relevant and easier to understand. With authorized customer behavior data, I would next evaluate whether the recommendations actually help people complete their searches.

## STAR answer
**Situation:** I was preparing a portfolio project to explore travel discovery and explainable personalization. [Confirm your personal motivation and timing.]

**Task:** I wanted a working experience that used real data, stayed understandable, and explained why a stay was recommended.

**Action:** I used a public D.C. listing snapshot, separated raw and processed data, and kept records with missing prices for analysis while excluding them from price-based searches. I separated essential requirements from preferences and used normalized scores. I also added tests for filters, scores, missing values, and empty searches. [Confirm which implementation and design decisions you personally made, and how you used coding assistance.]

**Result:** The project provides four working page flows and a transparent top-five recommendation list. The source snapshot contains 6,906 listings, and the updated automated suite passed 17 tests. I have not measured conversion or customer satisfaction. [Use the latest test results when discussing the redesign; do not claim browser or production validation unless completed.]

## Detailed technical explanation
I start in `src/clean_data.py`. `build_data()` downloads the pinned file if needed, reads it with pandas, and calls `clean_listings()`. I validate columns, remove only missing or duplicate IDs, parse prices, validate numeric fields, and create amenity flags. The processed data excludes host identities and source estimates of revenue or occupancy.

In `src/recommend.py`, `filter_listings()` enforces requirements with Boolean masks. `recommend()` assigns values between zero and one. The weights are 30% budget, 30% reviews, 20% amenities, 10% neighborhood, and 10% capacity. Unselected preference components are removed and remaining weights are rescaled. I sort by score, then price and ID for ties. `explain_match()` uses actual listing attributes to produce the explanations.

`src/analytics.py` calculates counts, medians, review averages, neighborhood summaries, and amenities. `app.py` connects widgets to those functions, caches data reads, and renders Plotly charts. The interface shows historical snapshot prices and makes missing information explicit.

## Five technical questions
**Why pandas?** I can express the cleaning, filters, groupings, and ranking directly with readable tables. This dataset does not need a database or a complex model.

**How do you handle missing prices?** I preserve the listing for other analysis, but it cannot satisfy a maximum-price search. I do not fill in a guessed price.

**How do you normalize the score?** I keep each component between zero and one, multiply by its weight, divide by the active weight total, and multiply by 100.

**How did you verify the ranking?** I check hard-filter compliance, score bounds, deterministic ordering, and an independently calculated score. I also test empty results and missing reviews.

**Why use the median price?** It is less sensitive to unusually high prices than the mean. I retain those listings in the data and label any chart-only trimming.

## Five behavioral and product questions
**Why this project for a digital experience role?** I wanted to connect data processing to something a visitor actually uses: finding options that fit their priorities.

**What tradeoff did you make?** I chose transparent rules that I can explain. They are easy to inspect, but they do not learn from customer behavior.

**What would you improve first?** I would ask people to try the search and explain whether the recommendations make sense. Then I would evaluate which preferences or explanations need improvement. I have not conducted that study yet.

**What would success look like?** I would define a measurable outcome such as completing a search or saving a relevant option, with appropriate privacy controls. I would compare it against a baseline before claiming improvement.

**Tell me about a difficult issue.** One documented tradeoff is incomplete prices: removing every incomplete record would reduce the analysis unnecessarily. The implementation keeps these records and excludes them only where a price is required. [Confirm whether this was a challenge you personally worked through; add your actual process rather than inventing a debugging story.]

## Connection to Marriott
I would connect StaySmart to the role's stated focus on personalization and digital experiences: collecting explicit preferences, respecting essential requirements, explaining recommendations, and using analytics to inform product decisions. I would not claim this reproduces Marriott's internal systems or uses its inventory. I would ask how the team evaluates relevance and balances experimentation with a consistent customer experience.

## Rules versus machine learning
My current system follows rules and weights that are explicitly defined in code. A machine-learning system would learn patterns from training data and would require suitable labels, validation, and monitoring. I chose rules because I have listing attributes but no authorized customer behavior or booking outcomes to train on. This is personalization based on stated preferences, not a trained recommendation model.


## A concise answer about the interface
I made the price and matching reasons easier to scan, and separated requirements from preferences. Someone can open “Why this stay?” to see exactly how the score was calculated. I would still want feedback from real users before claiming the design improves their experience.

## Before the interview
- Run the app and try a normal search, a search with no matches, and recommendations with and without preferences.
- Explain why a $250 maximum does not mean the algorithm tries to spend $250: cheaper eligible stays earn more budget points.
- Know that 6,906 is the listing count, not the number of customers or bookings.
- Confirm the bracketed STAR details and describe your own contribution accurately.
- Desktop/mobile visual review and live external links still need the checks noted in `VALIDATION.md`.

## Explaining the new features
“I added a way to compare up to three stays because a ranked list alone still leaves people switching between options. The comparison shows price, space, reviews, and reported amenities together. If someone changes a filter, the shortlist updates and removes options that no longer qualify.” [Confirm your personal contribution and explain coding assistance honestly.]

“How does it work?” — `compare_stays()` stores selected IDs in Streamlit session state and displays their rows in columns. `search_controls()` collects requirements, and Streamlit reruns the page after a widget change. `reset_filters()` clears the relevant widget keys. The ranking formula is unchanged; comparison does not award extra points.

“How did you add the branding?” — The logo is a small SVG pin with a hotel symbol. The same asset is used beside the name and as the favicon. One CSS file controls the navy, ivory, and lavender palette, spacing, labels, and mobile adjustments. There is no JavaScript framework.

## STAR example for the interface
**Situation:** The working project felt plain and text-heavy when I reviewed it.
**Task:** I wanted people to understand the results more easily while keeping the code simple enough to explain.
**Action:** The update adds clearer cards, reset controls, and a comparison panel using built-in Streamlit components. The score explanations still come from the existing recommendation logic. [Confirm the implementation work you personally did and where you used assistance.]
**Result:** The updated suite passed 16 automated tests, including comparisons and filter changes. I have not measured user satisfaction or conversion. Browser appearance still needs review on my own machine.

## Explaining the warning fix
“The page input had two initial values: one in session state and another in the widget. I made session state responsible for initialization and resets. I also checked that changing filters returns to page one and switching pages does not leave pagination empty.” [Describe your own contribution and coding assistance accurately.]

The latest visual update changes presentation only: an original skyline illustration, stronger card hierarchy, review badges, and larger match scores. The explanation text and score values still come from the same data and ranking code. No user-experience improvement has been measured.
