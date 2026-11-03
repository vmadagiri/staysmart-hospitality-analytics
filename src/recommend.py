"""Transparent rules and pandas scoring. No model or customer history."""
import pandas as pd
from src.clean_data import AMENITIES

WEIGHTS = {'budget_fit': .30, 'review_quality': .30, 'amenity_match': .20,
           'neighborhood_match': .10, 'capacity_fit': .10}


def filter_listings(data, budget, guests=1, bedrooms=0, neighborhoods=None,
                    property_types=None, min_review=0, required_amenities=None):
    matches = data.loc[data.price.notna() & data.price.le(budget)
                       & data.accommodates.ge(guests) & data.bedrooms.ge(bedrooms)].copy()
    if neighborhoods:
        matches = matches.loc[matches.neighborhood.isin(neighborhoods)]
    if property_types:
        matches = matches.loc[matches.property_type.isin(property_types)]
    if min_review > 0:
        matches = matches.loc[matches.review_score.ge(min_review)]
    for amenity in required_amenities or []:
        matches = matches.loc[matches[AMENITIES[amenity]].eq(True)]
    return matches


def recommend(data, budget, guests=1, bedrooms=0, min_review=0,
              required_amenities=None, preferred_amenities=None, preferred_neighborhoods=None,
              property_types=None):
    if budget <= 0:
        raise ValueError('Budget must be greater than zero.')
    matches = filter_listings(data, budget, guests, bedrooms, property_types=property_types,
                              min_review=min_review, required_amenities=required_amenities)
    # Each component is in [0, 1]. Higher means a closer fit.
    matches['budget_fit'] = (1 - matches.price / budget).clip(0, 1)
    matches['review_quality'] = matches.review_score.fillna(0).div(5).clip(0, 1)
    preferred_amenities = preferred_amenities or []
    preferred_neighborhoods = preferred_neighborhoods or []
    matches['amenity_match'] = 0.0
    if preferred_amenities:
        columns = [AMENITIES[amenity] for amenity in preferred_amenities]
        matches['amenity_match'] = matches[columns].astype(float).mean(axis=1)
    matches['neighborhood_match'] = matches.neighborhood.isin(preferred_neighborhoods).astype(float)
    matches['capacity_fit'] = (guests / matches.accommodates).clip(0, 1)
    # Unspecified preferences should not change the denominator or penalize anyone.
    active_weights = WEIGHTS.copy()
    if not preferred_amenities:
        active_weights.pop('amenity_match')
    if not preferred_neighborhoods:
        active_weights.pop('neighborhood_match')
    total_weight = sum(active_weights.values())
    matches['match_score'] = sum(matches[column] * weight for column, weight in active_weights.items()) / total_weight * 100
    matches['reasons'] = matches.apply(lambda row: explain_match(row, budget, guests, preferred_amenities,
                                                               preferred_neighborhoods), axis=1) if len(matches) else pd.Series(dtype=str)
    return matches.sort_values(['match_score', 'price', 'id'], ascending=[False, True, True]).head(5)


def explain_match(row, budget, guests, amenities, neighborhoods):
    reasons = [f"${row.price:,.0f} of your ${budget:,.0f} nightly budget"]
    reasons.append(f"{row.review_score:.2f}/5 review score" if pd.notna(row.review_score) else 'Review score unknown; no review points awarded')
    matched = [name for name in amenities if row[AMENITIES[name]]]
    if matched:
        reasons.append('Preferred amenities: ' + ', '.join(matched))
    if row.neighborhood in neighborhoods:
        reasons.append('In a preferred neighborhood')
    reasons.append(f"Fits {guests} guest(s); capacity {int(row.accommodates)}")
    return ' · '.join(reasons)
