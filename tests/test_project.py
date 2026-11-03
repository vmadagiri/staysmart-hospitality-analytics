"""Checks use real source rows; deliberate invalid edits are test fixtures only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.analytics import metrics, neighborhood_prices
from src.clean_data import COLUMNS, ROOT, build_data, clean_listings
from src.recommend import filter_listings, recommend


class DataAndRankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(ROOT / 'data/raw/listings.csv.gz', low_memory=False)
        cls.data, cls.audit = clean_listings(cls.raw)

    def test_source_and_counts(self):
        self.assertTrue(set(COLUMNS).issubset(self.raw.columns))
        self.assertEqual(len(self.data), self.audit['raw_records'] - self.audit['missing_ids_removed'] - self.audit['duplicate_ids_removed'])
        self.assertTrue(self.data.id.is_unique)
        self.assertGreater(self.data.latitude.between(38.79, 39).mean(), .99)
        self.assertGreater(self.data.longitude.between(-77.13, -76.90).mean(), .99)
        self.assertFalse(any('host_' in column for column in self.data.columns))

    def test_dirty_values_duplicates_and_missing_retained(self):
        rows = self.raw.iloc[:4].copy()
        rows.loc[rows.index[0], 'price'] = '$1,234.50'
        rows.loc[rows.index[1], 'price'] = '$0.00'
        rows.loc[rows.index[2], 'price'] = '-$10'
        rows.loc[rows.index[3], 'price'] = None
        rows.loc[rows.index[0], 'review_scores_rating'] = 8
        rows.loc[rows.index[0], 'latitude'] = 0
        rows.loc[rows.index[0], 'amenities'] = 'invalid JSON'
        dirty = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
        clean, audit = clean_listings(dirty)
        self.assertEqual(len(clean), 4)
        self.assertEqual(audit['duplicate_ids_removed'], 1)
        self.assertEqual(clean.price.notna().sum(), 1)
        self.assertAlmostEqual(clean.price.dropna().iloc[0], 1234.5)
        changed = clean.loc[clean.id.eq(rows.iloc[0].id)].iloc[0]
        self.assertTrue(pd.isna(changed.review_score))
        self.assertTrue(pd.isna(changed.latitude))
        self.assertFalse(changed.amenities_known)
        self.assertFalse(changed.has_wifi)

    def test_schema_failure_is_clear(self):
        with self.assertRaisesRegex(ValueError, 'missing required columns'):
            clean_listings(self.raw.drop(columns='amenities'))

    def test_filters_enforce_all_must_haves(self):
        available = self.data.loc[self.data.has_wifi & self.data.has_kitchen & self.data.price.notna() & self.data.review_score.ge(4)]
        example = available.iloc[0]
        result = filter_listings(self.data, budget=example.price, guests=1, bedrooms=0,
                                 neighborhoods=[example.neighborhood], property_types=[example.property_type],
                                 min_review=4, required_amenities=['Wi-Fi', 'Kitchen'])
        self.assertGreater(len(result), 0)
        self.assertTrue(result.price.le(example.price).all())
        self.assertTrue(result.neighborhood.eq(example.neighborhood).all())
        self.assertTrue(result.property_type.eq(example.property_type).all())
        self.assertTrue(result.review_score.ge(4).all())
        self.assertTrue((result.has_wifi & result.has_kitchen).all())

    def test_score_bounds_independent_calculation_and_determinism(self):
        top = recommend(self.data, 250, guests=2, preferred_amenities=['Wi-Fi', 'Kitchen'],
                        preferred_neighborhoods=[self.data.neighborhood.iloc[0]])
        self.assertEqual(len(top), 5)
        self.assertTrue(top.price.le(250).all())
        self.assertTrue(top.accommodates.ge(2).all())
        self.assertTrue(top.match_score.between(0, 100).all())
        self.assertTrue(top.match_score.is_monotonic_decreasing)
        row = top.iloc[0]
        expected = 100*(.3*(1-row.price/250) + .3*(0 if pd.isna(row.review_score) else row.review_score/5)
                        + .2*(int(row.has_wifi)+int(row.has_kitchen))/2
                        + .1*int(row.neighborhood == self.data.neighborhood.iloc[0]) + .1*2/row.accommodates)
        self.assertAlmostEqual(row.match_score, expected)
        pd.testing.assert_frame_equal(top, recommend(self.data, 250, guests=2, preferred_amenities=['Wi-Fi', 'Kitchen'], preferred_neighborhoods=[self.data.neighborhood.iloc[0]]))

    def test_no_preferences_rescales_and_missing_review_zero(self):
        candidates = self.data.loc[self.data.review_score.isna() & self.data.price.notna()]
        top = recommend(candidates, 100000)
        self.assertTrue(top.review_quality.eq(0).all())
        row = top.iloc[0]
        expected = 100*(.3*(1-row.price/100000)+.1/row.accommodates)/.7
        self.assertAlmostEqual(row.match_score, expected)
        self.assertIn('unknown', row.reasons)

    def test_empty_and_invalid_budget(self):
        self.assertTrue(recommend(self.data, .001).empty)
        self.assertTrue(filter_listings(self.data, budget=.001).empty)
        with self.assertRaises(ValueError):
            recommend(self.data, 0)

    def test_metrics_match_direct_calculations(self):
        result = metrics(self.data)
        self.assertEqual(result['listings'], len(self.raw))
        raw_prices = pd.to_numeric(self.raw.price.str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
        self.assertEqual(result['median_price'], raw_prices[raw_prices.gt(0)].median())
        summary = neighborhood_prices(self.data)
        self.assertEqual(summary.listings.sum(), result['priced_listings'])
        self.assertAlmostEqual(result['average_review'], self.data.review_score.dropna().mean())

    def test_disk_roundtrip(self):
        saved = pd.read_csv(ROOT / 'data/processed/listings.csv.gz')
        self.assertEqual(len(saved), len(self.data))
        self.assertEqual(saved.price.median(), self.data.price.median())
        self.assertEqual(saved.id.tolist(), self.data.id.tolist())

    def test_offline_download_failure_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('src.clean_data.urlretrieve', side_effect=OSError('offline')):
                with self.assertRaises(OSError):
                    build_data(Path(folder))
            self.assertFalse((Path(folder)/'data/processed/listings.csv.gz').exists())


class AppTests(unittest.TestCase):
    def test_pages_empty_states_and_chart_filters(self):
        app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=40).run()
        self.assertEqual(len(app.exception), 0)
        app.number_input(key='discover_budget').set_value(1).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('No stays match' in item.value for item in app.info))
        app.button(key='nav_Personalized Picks').click().run()
        self.assertEqual(len(app.exception), 0)
        app.number_input(key='picks_budget').set_value(1).run()
        self.assertTrue(any('No stays meet' in item.value for item in app.info))
        app.button(key='nav_Market Insights').click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, '6,906')
        self.assertEqual(app.metric[1].value, '$213.50')
        app.multiselect(key='market_types').set_value(['Entire home/apt' if 'Entire home/apt' in app.multiselect(key='market_types').options else app.multiselect(key='market_types').options[0]]).run()
        self.assertEqual(len(app.exception), 0)
        expected = pd.read_csv(ROOT/'data/processed/listings.csv.gz')
        expected = expected.loc[expected.property_type.isin(app.multiselect(key='market_types').value)]
        self.assertEqual(app.metric[0].value, f'{len(expected):,}')
        app.multiselect(key='market_types').set_value([]).run()
        app.number_input(key='market_budget').set_value(1).run()
        app.checkbox[0].uncheck().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('No listings match' in item.value for item in app.info))
        app.button(key='nav_Behind the Data').click().run()
        self.assertEqual(len(app.exception), 0)


if __name__ == '__main__':
    unittest.main()
