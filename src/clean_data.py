"""Download once, inspect the official schema, and clean without inventing values."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = '2026-09-19'
SOURCE_URL = f'https://data.insideairbnb.com/united-states/dc/washington-dc/{SNAPSHOT}/data/listings.csv.gz'
COLUMNS = ['id', 'name', 'neighbourhood_cleansed', 'property_type', 'room_type',
           'latitude', 'longitude', 'accommodates', 'bedrooms', 'amenities', 'price',
           'review_scores_rating', 'number_of_reviews', 'minimum_nights',
           'availability_30', 'availability_60', 'availability_90', 'availability_365', 'last_scraped']
AMENITIES = {'Wi-Fi': 'has_wifi', 'Kitchen': 'has_kitchen', 'Parking (paid or free)': 'has_parking'}


def parse_amenities(value):
    """Keep unknown amenity data separate from a known empty list."""
    if not isinstance(value, str):
        return None
    try:
        items = json.loads(value)
        return [item for item in items if isinstance(item, str)] if isinstance(items, list) else None
    except (ValueError, TypeError):
        return None


def clean_listings(raw):
    missing = sorted(set(COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f'Official schema is missing required columns: {missing}')
    data = raw[COLUMNS].copy()
    audit = {'raw_records': len(data), 'raw_columns': list(raw.columns),
             'raw_missing_values': data.isna().sum().astype(int).to_dict()}
    data['id'] = pd.to_numeric(data['id'], errors='coerce').astype('Int64')
    before = len(data)
    data = data.dropna(subset=['id'])
    audit['missing_ids_removed'] = before - len(data)
    before = len(data)
    data = data.drop_duplicates(subset=['id'], keep='first')
    audit['duplicate_ids_removed'] = before - len(data)
    data = data.rename(columns={'neighbourhood_cleansed': 'neighborhood',
                                'review_scores_rating': 'review_score'})
    # Currency symbols and thousands separators are formatting, not numeric values.
    data['price'] = pd.to_numeric(data['price'].astype('string').str.replace('$', '', regex=False)
                                  .str.replace(',', '', regex=False), errors='coerce')
    audit['nonpositive_prices'] = int(data['price'].le(0).sum())
    data.loc[data['price'].le(0) | data['price'].eq(float('inf')), 'price'] = float('nan')
    numeric = ['accommodates', 'bedrooms', 'review_score', 'latitude', 'longitude',
               'number_of_reviews', 'minimum_nights', 'availability_30', 'availability_60',
               'availability_90', 'availability_365']
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors='coerce')
    data.loc[~data['review_score'].between(0, 5), 'review_score'] = float('nan')
    # A zero rating with no reviews is unknown, rather than evidence of poor quality.
    data.loc[data['number_of_reviews'].fillna(0).le(0), 'review_score'] = float('nan')
    data.loc[data['accommodates'].lt(1), 'accommodates'] = float('nan')
    data.loc[data['bedrooms'].lt(0), 'bedrooms'] = float('nan')
    for days in [30, 60, 90, 365]:
        column = f'availability_{days}'
        data.loc[~data[column].between(0, days), column] = float('nan')
    # A broad D.C. extent is a sanity check, not a precise district boundary test.
    valid_location = data['latitude'].between(38.79, 39.00) & data['longitude'].between(-77.13, -76.90)
    audit['coordinates_excluded_from_map'] = int((~valid_location).sum())
    data.loc[~valid_location, ['latitude', 'longitude']] = float('nan')
    for column, fallback in [('name', 'Unnamed listing'), ('neighborhood', 'Not reported'),
                             ('property_type', 'Not reported'), ('room_type', 'Not reported')]:
        data[column] = data[column].fillna(fallback).replace(r'^\s*$', fallback, regex=True)
    items = data['amenities'].apply(parse_amenities)
    data['amenities_known'] = items.notna()
    data['amenities'] = items.apply(lambda value: json.dumps(value if value is not None else []))
    data['has_wifi'] = items.apply(lambda value: any(a.lower() in ['wifi', 'wi-fi', 'wireless internet'] for a in (value or [])))
    data['has_kitchen'] = items.apply(lambda value: any(a.lower() == 'kitchen' for a in (value or [])))
    data['has_parking'] = items.apply(lambda value: any('parking' in a.lower() and not a.lower().startswith('no ') for a in (value or [])))
    data = data.sort_values('id').reset_index(drop=True)
    audit.update({'cleaned_records': len(data), 'searchable_price_records': int(data.price.notna().sum()),
                  'cleaned_missing_values': data.isna().sum().astype(int).to_dict(),
                  'price_p99': float(data.price.quantile(.99)),
                  'scrape_dates': sorted(data.last_scraped.dropna().unique().tolist())})
    return data, audit


def build_data(root=ROOT):
    raw_path = root / 'data/raw/listings.csv.gz'
    output = root / 'data/processed'
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        temporary = raw_path.with_suffix('.download')
        try:
            urlretrieve(SOURCE_URL, temporary)
            temporary.replace(raw_path)
        finally:
            temporary.unlink(missing_ok=True)
    raw = pd.read_csv(raw_path, low_memory=False)
    cleaned, audit = clean_listings(raw)
    audit.update({'source': 'Inside Airbnb', 'city': 'Washington, D.C., United States',
                  'snapshot_date': SNAPSHOT, 'download_url': SOURCE_URL,
                  'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                  'raw_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest()})
    # Only allowlisted property fields are written; no host or reviewer identities.
    cleaned.to_csv(output / 'listings.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    (output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    return cleaned, audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    frame, report = build_data()
    print(f"Cleaned {report['raw_records']:,} → {len(frame):,} listings; {report['searchable_price_records']:,} have valid prices.")
