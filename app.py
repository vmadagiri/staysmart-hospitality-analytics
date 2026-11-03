"""StaySmart: public listing discovery with explainable preference matching."""
import json
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import common_amenities, metrics, neighborhood_prices, verified_findings
from src.clean_data import AMENITIES, ROOT, SNAPSHOT, SOURCE_URL, build_data
from src.recommend import WEIGHTS, filter_listings, recommend

st.set_page_config(page_title='StaySmart | Explore smarter. Stay better.', page_icon=str(ROOT / 'assets/logo.svg'), layout='wide')
st.markdown('<style>' + (ROOT / 'assets/style.css').read_text() + '</style>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data():
    processed = ROOT / 'data/processed/listings.csv.gz'
    audit_path = ROOT / 'data/processed/audit.json'
    if not processed.exists() or not audit_path.exists():
        return build_data()
    frame = pd.read_csv(processed)
    return frame, json.loads(audit_path.read_text())


try:
    with st.spinner('Preparing the D.C. snapshot. The first visit may take a moment…'):
        data, audit = load_data()
except Exception:
    st.error('The D.C. data could not be loaded. Please try again later. If you run this project locally, run: python -m src.clean_data')
    st.caption('StaySmart uses the official Inside Airbnb download. No sample data is substituted.')
    st.stop()

logo = (ROOT / 'assets/logo.svg').read_text()
st.markdown(f'<div class="wordmark"><div class="brand">{logo}StaySmart</div><span>WASHINGTON, D.C. / STAYS WITH PERSPECTIVE</span></div>', unsafe_allow_html=True)
pages = ['Discover Stays', 'Personalized Picks', 'Market Insights', 'Behind the Data']
if 'navigation' not in st.session_state:
    st.session_state.navigation = pages[0]
def navigate(title):
    st.session_state.navigation = title


for column, title in zip(st.columns(4), pages):
    column.button(title, key='nav_' + title, width='stretch',
                  type='primary' if st.session_state.navigation == title else 'secondary',
                  on_click=navigate, args=(title,))
page = st.session_state.navigation

titles = {'Discover Stays': 'Explore smarter. Stay better.', 'Personalized Picks': 'A stay that fits your priorities.', 'Market Insights': 'The D.C. market, in context.', 'Behind the Data': 'Know what is behind each result.'}
descriptions = {
    'Discover Stays': "Find stays that fit your priorities, see why they match, and explore the data behind Washington, D.C.’s short-term rental market.",
    'Personalized Picks': 'Set your requirements. Add your preferences. See why each stay makes the shortlist.',
    'Market Insights': 'Explore listing prices, neighborhoods, and amenities in one D.C. snapshot.',
    'Behind the Data': 'See the source, cleaning decisions, and limits behind every result.'
}
travel_art = (ROOT / 'assets/travel.svg').read_text()
st.markdown(f'<section class="hero"><div class="hero-copy"><div class="eyebrow">WASHINGTON, D.C. / {page}</div><h1>{titles[page]}</h1><p>{descriptions[page]}</p><div class="hero-note">YOUR BUDGET &nbsp; / &nbsp; YOUR PRIORITIES &nbsp; / &nbsp; CLEAR CHOICES</div></div><div class="travel-art">{travel_art}<span>THE DISTRICT, REIMAGINED · ORIGINAL ILLUSTRATION</span></div></section>', unsafe_allow_html=True)
st.caption(f'Inside Airbnb · September 19, 2026 snapshot · USD · Historical listing prices, not live quotes or confirmed availability.')


def choices(column):
    return sorted(data[column].dropna().unique().tolist())


def reset_filters(prefix):
    # Callbacks run before Streamlit redraws the widgets.
    for key in list(st.session_state):
        if key.startswith(prefix) or key == 'preferred_amenities' and prefix == 'picks_':
            del st.session_state[key]


def search_controls(prefix, recommendation=False):
    st.subheader('Your trip, your priorities' if recommendation else 'Make room for your kind of stay')
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    budget = c1.number_input('Maximum nightly price (USD)', min_value=1, max_value=100000, value=250, step=25, key=prefix+'budget')
    guests = c2.number_input('Guests', min_value=1, max_value=16, value=2, key=prefix+'guests')
    bedrooms = c3.number_input('Minimum bedrooms', min_value=0, max_value=16, value=0, key=prefix+'bedrooms')
    review = c4.selectbox('Minimum review score', [0.0, 3.0, 4.0, 4.5, 4.8], key=prefix+'review',
                          format_func=lambda x: 'Any / unknown OK' if x == 0 else f'{x:.1f}/5')
    with st.expander('Location, property type & amenities', expanded=recommendation):
        c1, c2 = st.columns(2)
        neighborhoods = c1.multiselect('Preferred neighborhoods' if recommendation else 'Neighborhoods', choices('neighborhood'), key=prefix+'neighborhoods')
        properties = c2.multiselect('Property types', choices('property_type'), key=prefix+'types')
        required = st.multiselect('Must-have amenities', list(AMENITIES), key=prefix+'required')
        st.caption('Parking may be paid or free. A review minimum excludes unknown scores. Zero bedrooms includes studios.')
        if recommendation:
            st.caption('Neighborhoods are preferences: other areas can still appear. Property types and must-have amenities are requirements.')
    st.button('Reset filters', key=prefix+'reset', on_click=reset_filters, args=(prefix,))
    return dict(budget=budget, guests=guests, bedrooms=bedrooms, min_review=review,
                neighborhoods=neighborhoods, property_types=properties, required_amenities=required)


def listing_card(row, ranked=False, preferred_amenities=None, preferred_neighborhoods=None):
    with st.container(border=True):
        st.markdown('<div class="stay-art" aria-label="Generic building illustration"><div class="townhouse"><i></i><i></i><i></i></div><span class="art-label">STAYSMART · ILLUSTRATION, NOT A PROPERTY PHOTO</span></div>', unsafe_allow_html=True)
        if ranked:
            st.markdown(f'<div class="match">{row.match_score:.1f}<small>/ 100<span>YOUR PREFERENCE MATCH</span></small></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="listing-label">{escape(str(row.property_type))}</div><div class="listing-title">{escape(str(row["name"]))}</div><div class="listing-label">{escape(str(row.neighborhood))}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="price">${row.price:,.2f} <span>/ night · snapshot price</span></div>', unsafe_allow_html=True)
        score = f'{row.review_score:.2f}/5' if pd.notna(row.review_score) else 'Not reported'
        st.markdown(f'<div class="stay-facts">♙ {int(row.accommodates)} guests &nbsp; ▤ {int(row.bedrooms)} bedrooms <strong>★ {score}</strong></div>', unsafe_allow_html=True)
        amenities = json.loads(row.amenities)
        tags = ''.join(f'<span class="tag">✓ {escape(item)}</span>' for item in amenities[:4])
        st.markdown(f'<div class="tags">{tags or ('No amenities reported' if row.amenities_known else 'Amenities unknown')}</div>', unsafe_allow_html=True)
        if ranked:
            for reason in row.reasons.split(' · ')[:3]:
                st.markdown(f'<div class="match-reason"><span>✓</span>{escape(reason)}</div>', unsafe_allow_html=True)
        st.link_button('View listing ↗', f'https://www.airbnb.com/rooms/{int(row.id)}')
        st.caption(f'{len(amenities)} reported amenities · expand below for all details')
        with st.expander('Why this stay?' if ranked else 'More listing details'):
            st.write(str(row['name']))
            if ranked:
                st.write(row.reasons)
                weights = WEIGHTS.copy()
                if not preferred_amenities:
                    weights.pop('amenity_match')
                if not preferred_neighborhoods:
                    weights.pop('neighborhood_match')
                for component, weight in weights.items():
                    points = 100 * row[component] * weight / sum(weights.values())
                    st.progress(float(row[component]), text=f'{component.replace("_", " ").title()} · {row[component]:.3f} × {100*weight/sum(weights.values()):.1f}% = {points:.2f} points')
                st.caption('This is a preference score, not a probability or quality guarantee. Bars show normalized component values. Points add to the match score before rounding. Unselected preferences are excluded.')
            st.write('Reported amenities: ' + (', '.join(amenities) if amenities else ('None listed' if row.amenities_known else 'Unknown')))
            if pd.notna(row.minimum_nights):
                st.write(f'Minimum stay in snapshot: {int(row.minimum_nights)} nights. Trip dates and stay eligibility are not checked.')
            st.caption('Historical listing information. Check current details with the original listing.')


def compare_stays(results, prefix):
    with st.expander('Compare stays · choose up to three'):
        if results.empty:
            st.info('Broaden your filters to find stays to compare.')
            return
        lookup = results.set_index('id')
        key = prefix + 'compare'
        # Remove selections that no longer satisfy the current filters.
        st.session_state[key] = [item for item in st.session_state.get(key, []) if item in lookup.index]
        selected = st.multiselect('Choose stays', lookup.index.tolist(), key=key, max_selections=3,
                                  format_func=lambda item: f"{lookup.loc[item, 'name']} · ${lookup.loc[item, 'price']:,.2f} · #{item}")
        if not selected:
            st.caption('Compare price, reviews, space, and amenities side by side.')
            return
        for column, listing_id in zip(st.columns(len(selected)), selected):
            row = lookup.loc[listing_id]
            with column:
                st.markdown('**' + str(row['name']) + '**')
                st.metric('Snapshot price / night', f'${row.price:,.2f}')
                st.write(row.neighborhood)
                st.write(row.property_type)
                st.write(f'{int(row.accommodates)} guests · {int(row.bedrooms)} bedrooms')
                st.write(f'Review: {row.review_score:.2f}/5' if pd.notna(row.review_score) else 'Review: not reported')
                if 'match_score' in row.index:
                    st.metric('Preference match / 100', f'{row.match_score:.1f}')
                for label, field in AMENITIES.items():
                    status = 'Reported' if row[field] else ('Not reported' if row.amenities_known else 'Unknown')
                    st.write(f'{label}: {status}')
                with st.expander('All reported amenities'):
                    st.write(', '.join(json.loads(row.amenities)) or 'None reported')


def draw_chart(figure):
    figure.update_layout(font=dict(family='Arial', color='#192c45'), paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='#ffffff', margin=dict(l=12, r=12, t=45, b=20),
                         colorway=['#7777b0', '#98b7cc', '#c5b6d6', '#586f91'])
    figure.update_layout(font_size=14, title_font=dict(size=21, family='Georgia', color='#192c45'), bargap=.28, hoverlabel=dict(bgcolor='#ffffff', font_color='#192c45'))
    figure.update_xaxes(automargin=True, gridcolor='#e8e5df')
    figure.update_yaxes(automargin=True, gridcolor='#e8e5df')
    with st.container(border=True):
        st.plotly_chart(figure, width='stretch', config={'displaylogo': False, 'scrollZoom': False})


if page == 'Discover Stays':
    filters = search_controls('discover_')
    results = filter_listings(data, **filters)
    st.divider()
    left, right = st.columns([2, 1])
    left.subheader(f'{len(results):,} stays fit your search')
    sort_by = right.selectbox('Sort by', ['Lowest price', 'Highest review score', 'Highest price'])
    column, ascending = {'Lowest price': ('price', True), 'Highest review score': ('review_score', False),
                         'Highest price': ('price', False)}[sort_by]
    results = results.sort_values([column, 'id'], ascending=[ascending, True], na_position='last')
    compare_stays(results, 'discover_')
    if results.empty:
        st.info('No stays match these choices. Try a higher budget or fewer must-haves.')
    else:
        pages = (len(results) + 8) // 9
        signature = (tuple(results.id), sort_by)
        if st.session_state.get('search_signature') != signature or 'discover_page' not in st.session_state:
            st.session_state['discover_page'] = 1
            st.session_state['search_signature'] = signature
        # Session state owns initialization; value=None avoids a second default.
        current = st.number_input('Results page', min_value=1, max_value=pages, value=None, key='discover_page')
        if current is None:
            st.info('Enter a results page to continue.')
            st.stop()
        visible = results.iloc[(current-1)*9:current*9]
        columns = st.columns(3)
        for index, (_, row) in enumerate(visible.iterrows()):
            with columns[index % 3]:
                listing_card(row)
        st.caption(f'Showing {(current-1)*9+1}–{min(current*9, len(results))} of {len(results):,}.')

elif page == 'Personalized Picks':
    filters = search_controls('picks_', recommendation=True)
    preferred_neighborhoods = filters.pop('neighborhoods')
    preferred = st.multiselect('Nice-to-have amenities', list(AMENITIES), key='preferred_amenities')
    top = recommend(data, **filters, preferred_amenities=preferred, preferred_neighborhoods=preferred_neighborhoods)
    st.divider()
    st.subheader(f'Your top {len(top)} matches' if len(top) else 'Your matches')
    st.write('Clear reasons let you decide whether a recommendation fits your trip, rather than relying on a score alone.')
    st.write('Your budget, guest count, bedrooms, review minimum, property type, and must-haves are firm requirements. Preferred neighborhoods and nice-to-haves help rank the remaining stays.')
    if top.empty:
        st.info('No stays meet your essential requirements. Try relaxing your budget, review minimum, or must-haves.')
    compare_stays(top, 'picks_')
    for _, row in top.iterrows():
        listing_card(row, ranked=True, preferred_amenities=preferred, preferred_neighborhoods=preferred_neighborhoods)
    with st.expander('How the scoring works'):
        st.write('Each part scores from 0 to 1. Budget fit rewards a lower price within your budget. Reviews use the reported score divided by 5; unknown scores earn zero review points. Amenities measure the share of your nice-to-haves reported. Neighborhood earns 1 for a preferred area and 0 otherwise. Capacity uses guests ÷ listing capacity, rewarding a closer size fit.')
        st.table(pd.DataFrame({'Component': ['Budget fit', 'Review score', 'Amenity matches', 'Preferred neighborhood', 'Capacity fit'],
                               'Base weight': ['30%', '30%', '20%', '10%', '10%']}))
        st.write('Unused amenity and neighborhood components are removed, and remaining weights are rescaled to total 100%. Ties use lower price, then listing ID. The weights are design choices, not learned from guest behavior.')
        st.code('match_score = 100 * weighted_component_sum / active_weight_sum', language='python')

elif page == 'Market Insights':
    st.subheader('Understand the D.C. listing landscape')
    c1, c2 = st.columns(2)
    areas = c1.multiselect('Neighborhoods', choices('neighborhood'), key='market_areas')
    types = c2.multiselect('Property types', choices('property_type'), key='market_types')
    guests = c1.number_input('Minimum guest capacity', min_value=1, max_value=16, value=1, key='market_guests')
    review = c2.selectbox('Minimum review score', [0.0, 4.0, 4.5, 4.8], key='market_review')
    required = st.multiselect('Required amenities', list(AMENITIES), key='market_amenities')
    price_cap = st.number_input('Maximum nightly price (USD)', min_value=1, max_value=100000, value=100000, key='market_budget')
    st.button('Reset market filters', on_click=reset_filters, args=('market_',))
    include_unknown = st.checkbox('Include listings with unreported prices', value=True, key='market_unknown')
    filtered = data.loc[data.accommodates.ge(guests)].copy()
    if areas:
        filtered = filtered.loc[filtered.neighborhood.isin(areas)]
    if types:
        filtered = filtered.loc[filtered.property_type.isin(types)]
    if review:
        filtered = filtered.loc[filtered.review_score.ge(review)]
    for name in required:
        filtered = filtered.loc[filtered[AMENITIES[name]]]
    filtered = filtered.loc[filtered.price.le(price_cap) | (filtered.price.isna() & include_unknown)]
    st.caption('Every chart and metric below uses these filters. Missing prices are retained only when selected; price statistics always exclude them.')
    if filtered.empty:
        st.info('No listings match these filters. Broaden your selections to see the market.')
    else:
        summary = metrics(filtered)
        cards = st.columns(4)
        cards[0].metric('Listings analyzed', f"{summary['listings']:,}")
        cards[1].metric('Median nightly price', f"${summary['median_price']:,.2f}" if pd.notna(summary['median_price']) else 'Not reported')
        cards[2].metric('Average review score', f"{summary['average_review']:.2f}/5" if pd.notna(summary['average_review']) else 'Not reported')
        cards[3].metric('Listings with prices', f"{summary['priced_listings']:,}")
        st.caption(f"Review average is per listing, based on {summary['rated_listings']:,} reported scores; it is not weighted by number of reviews.")
        st.subheader('Which neighborhoods have the most listings?')
        counts = filtered.neighborhood.value_counts().head(12).rename_axis('Neighborhood').reset_index(name='Listings')
        draw_chart(px.bar(counts.sort_values('Listings'), x='Listings', y='Neighborhood', orientation='h', title='Top 12 neighborhoods by listing count', height=460))
        st.subheader('How do nightly prices vary?')
        chart_data = filtered.dropna(subset=['price'])
        trim = st.checkbox('Limit price charts to the filtered 99th percentile', value=True)
        if not chart_data.empty:
            cap = chart_data.price.quantile(.99) if trim else chart_data.price.max()
            displayed = chart_data.loc[chart_data.price.le(cap)]
            st.caption(f'{len(chart_data)-len(displayed):,} higher-price listings hidden from these two price charts only. Metrics use the full filtered data. Chart ceiling: ${cap:,.2f}.')
            draw_chart(px.histogram(displayed, x='price', nbins=50, labels={'price': 'Nightly listing price (USD)'}, title='Nightly price distribution'))
            areas_to_show = displayed.neighborhood.value_counts().head(12).index
            st.caption('Price spreads below show the 12 neighborhoods with the most listings in the displayed price range. All areas remain in the full summary.')
            draw_chart(px.box(displayed.loc[displayed.neighborhood.isin(areas_to_show)], x='price', y='neighborhood', points=False,
                              height=500,
                              labels={'price': 'Nightly listing price (USD)', 'neighborhood': 'Neighborhood'}, title='Price spread by neighborhood'))
            with st.expander('Full neighborhood price summary'):
                st.dataframe(neighborhood_prices(filtered), hide_index=True, width='stretch')
        else:
            st.info('No reported prices in this selection.')
        c1, c2 = st.columns(2)
        with c1:
            amenities = common_amenities(filtered).head(12)
            if len(amenities):
                draw_chart(px.bar(amenities.sort_values('listings'), x='listings', y='amenity', orientation='h', title='Most reported amenities', labels={'listings': 'Listings reporting amenity', 'amenity': ''}, height=460))
            else:
                st.info('No reported amenities in this selection.')
        with c2:
            properties = filtered.property_type.value_counts().head(12).rename_axis('property_type').reset_index(name='listings')
            draw_chart(px.bar(properties.sort_values('listings'), x='listings', y='property_type', orientation='h', title='Leading property types', labels={'listings': 'Listing count', 'property_type': ''}, height=460))
        review_data = filtered.dropna(subset=['review_score'])
        if len(review_data):
            draw_chart(px.histogram(review_data, x='review_score', nbins=25, title='Reported review scores', labels={'review_score': 'Review score (0–5)'}))
        st.subheader('Calendar availability in the snapshot')
        windows = [30, 60, 90, 365]
        availability = pd.DataFrame({'Window': [f'Next {days} days' for days in windows],
                                     'Reported available days (%)': [filtered[f'availability_{days}'].mean()/days*100 for days in windows]})
        draw_chart(px.bar(availability, x='Window', y='Reported available days (%)', range_y=[0, 100], title='Average share of days marked available'))
        st.caption('Uses summary availability fields from detailed listings, not a separate calendar download. Windows overlap and start at the scrape date. Unavailable days may be booked, blocked, or otherwise unavailable; they do not establish occupancy or bookings.')
        locations = filtered.dropna(subset=['latitude', 'longitude'])
        st.caption(f'{len(locations):,} listings with valid coordinates. Locations are approximate. Background tiles use OpenStreetMap; no API key is required.')
        plain_map = st.checkbox('Use a plain map background if map tiles do not load', value=False)
        if len(locations):
            draw_chart(px.scatter_map(locations, title='Washington, D.C. listing locations', lat='latitude', lon='longitude', hover_name='name', hover_data={'neighborhood': True, 'price': ':$.2f', 'review_score': ':.2f', 'accommodates': True, 'latitude': False, 'longitude': False},
                                      labels={'price': 'Nightly price (USD)', 'review_score': 'Review / 5', 'accommodates': 'Guest capacity', 'neighborhood': 'Neighborhood'},
                                      zoom=10, height=510, map_style='white-bg' if plain_map else 'open-street-map', opacity=.35,
                                      color_discrete_sequence=['#6868a6']))

else:
    st.subheader('Behind the Data')
    st.markdown('### Problem')
    st.write('A long list of stays can make travel planning harder. StaySmart explores how clear filters and explainable rankings can help visitors find options that fit their needs.')
    st.markdown('### Approach')
    st.markdown('<ol class="pipeline" aria-label="Data pipeline"><li>Inside Airbnb dataset</li><li>Python cleaning</li><li>Processed data</li><li>Filters and scoring</li><li>Streamlit interface</li></ol>', unsafe_allow_html=True)
    st.write('Recommendations apply firm requirements first, then combine budget (30%), reviews (30%), preferred amenities (20%), neighborhood (10%), and capacity (10%). Unselected preferences are removed and active weights are rescaled. See Personalized Picks for each listing’s actual calculation.')
    st.write('Use real Washington, D.C. accommodation listings, clean them with pandas, and separate firm requirements from preferences. Show the market context alongside the results.')
    st.write(f"Source: Inside Airbnb, Washington, D.C., United States. Published snapshot: {SNAPSHOT}. Actual scrape dates: {', '.join(audit['scrape_dates'])}.")
    st.markdown(f'[Official data page](https://insideairbnb.com/get-the-data/) · [Original detailed CSV]({SOURCE_URL}) · [Source assumptions](https://insideairbnb.com/data-assumptions/)')
    st.write(f"Records: {audit['raw_records']:,} before → {audit['cleaned_records']:,} after cleaning. Duplicate listing IDs removed: {audit['duplicate_ids_removed']:,}. Missing IDs removed: {audit['missing_ids_removed']:,}.")
    with st.expander('Cleaning decisions and missing values', expanded=False):
        st.write('Keep a listing unless its ID is missing or duplicated. Parse USD prices and mark nonpositive or invalid prices unknown. Retain unknown prices for non-price analysis. Search requires a valid price, guest capacity, and bedroom count; unknowns are never filled with guessed numbers. Studios may have zero bedrooms.')
        st.write('Keep unknown review scores. Treat a score without any reviews as unknown. Require scores within 0–5. Invalid capacities, bedrooms, availability counts, and map coordinates become missing values. Missing amenities are flagged as unknown; they cannot satisfy a must-have. Parking includes paid and free options, including street parking.')
        st.write('Retain high prices in the cleaned data. Price charts can hide values above their filtered 99th percentile; metrics do not trim them. Coordinates use a broad D.C. bounding box as a sanity check, not a precise boundary test. Host identities, review text, source estimates of revenue, and source estimates of occupancy are excluded from processed data.')
        st.dataframe(pd.DataFrame({'Field': list(audit['cleaned_missing_values']), 'Missing after cleaning': list(audit['cleaned_missing_values'].values())}), hide_index=True, width='stretch')
        st.caption('Raw schema, raw missing counts, scrape dates, and file checksum are recorded in data/processed/audit.json after the pipeline runs.')
    st.markdown('### Results')
    st.caption('These three findings use the full cleaned snapshot, independently of filters on other pages.')
    for finding in verified_findings(data):
        st.write('• ' + finding)
    st.markdown('### Limitations')
    st.write('This is a historical snapshot of Airbnb listings, not Marriott inventory or a booking service. Prices exclude any unreported fees and may use different stay conditions. Reviews and reported amenities can be incomplete. Locations are approximate. Listings may have changed since collection.')
    st.write('Availability is not proof of a booking. No bookings, confirmed revenue, occupancy, cancellation rates, conversion rates, or customer identities are inferred. The ranking weights are unvalidated design choices; missing reviews receive no review points and may disadvantage new listings.')
    st.write('With authorized booking and customer behavior data, a future version could evaluate ranking quality, measure search completion, test whether clear explanations help visitors, and compare designs in an A/B test. This project does not measure those outcomes.')
    st.markdown('### About')
    st.write('Built by Vaishnavi Madagiri, a Data Science graduate student at Virginia Tech, to explore travel discovery, data quality, and simple personalization. This independent portfolio project is not affiliated with Airbnb or Marriott.')
    st.markdown('[Vaishnavi on GitHub](https://github.com/vmadagiri)')
    st.markdown('### Attribution')
    st.write(f'Data: Inside Airbnb, Washington, D.C., {SNAPSHOT} detailed listings snapshot. Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). StaySmart selects fields, cleans values, aggregates statistics, and adds preference scores. No endorsement is implied.')
    st.markdown('[CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/) · [Inside Airbnb data policies](https://insideairbnb.com/data-policies/)')
    st.caption('The source asks users not to republish its data. Raw and processed files are excluded from Git. Deployment downloads the pinned official source once and caches it locally; no data-download feature is provided. Listing photos are omitted because the data license does not establish rights to third-party photos.')

st.markdown('<div class="footer">✦ StaySmart · Built by <a href="https://github.com/vmadagiri">Vaishnavi Madagiri</a><br>Data: <a href="https://insideairbnb.com/get-the-data/">Inside Airbnb</a>, Washington, D.C., September 19, 2026 · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · Selected, cleaned, and summarized.<br>Independent portfolio project. Not affiliated with Marriott or Airbnb.</div>', unsafe_allow_html=True)
