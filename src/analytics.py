"""Small summaries shared by the app, README generation, and checks."""
import json
import pandas as pd


def metrics(data):
    return {'listings': len(data), 'priced_listings': int(data.price.notna().sum()),
            'median_price': data.price.dropna().median() if data.price.notna().any() else float('nan'),
            'average_review': data.review_score.mean(),
            'rated_listings': int(data.review_score.notna().sum())}


def neighborhood_prices(data):
    return (data.dropna(subset=['price']).groupby('neighborhood')['price']
            .agg(listings='count', median_price='median').reset_index()
            .sort_values('median_price', ascending=False))


def common_amenities(data):
    items = data['amenities'].apply(json.loads).apply(lambda values: list(set(values))).explode().dropna()
    return items.value_counts().rename_axis('amenity').reset_index(name='listings')


def verified_findings(data):
    summary = metrics(data)
    entire = int(data.room_type.eq('Entire home/apt').sum())
    return [f"{summary['priced_listings']:,} of {len(data):,} listings have a valid nightly price; their median is ${summary['median_price']:,.2f}.",
            f"{entire:,} listings ({entire / len(data):.1%}) are classified as entire homes or apartments.",
            f"{summary['rated_listings']:,} listings have a reported review score; their listing-weighted average is {summary['average_review']:.2f}/5."]
