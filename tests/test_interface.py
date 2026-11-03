"""Regression checks for recommendation explanations and real-data UI states."""
import re
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.clean_data import ROOT
from src.recommend import recommend


class InterfaceTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()

    def test_displayed_points_reconcile_for_all_preference_modes(self):
        data = pd.read_csv(ROOT / 'data/processed/listings.csv.gz')
        area = data.neighborhood.iloc[0]
        app = self.app()
        app.button(key='nav_Personalized Picks').click().run()
        for amenities, areas in [([], []), (['Wi-Fi'], []), ([], [area]), (['Wi-Fi'], [area])]:
            app.multiselect(key='preferred_amenities').set_value(amenities)
            app.multiselect(key='picks_neighborhoods').set_value(areas).run()
            self.assertEqual(len(app.exception), 0)
            top = recommend(data, 250, guests=2, preferred_amenities=amenities,
                            preferred_neighborhoods=areas)
            count = 3 + bool(amenities) + bool(areas)
            bars = app.get('progress')
            self.assertEqual(len(bars), len(top) * count)
            for position, (_, row) in enumerate(top.iterrows()):
                points = [float(re.search(r'= ([\d.]+) points', item.proto.text).group(1))
                          for item in bars[position*count:(position+1)*count]]
                self.assertAlmostEqual(sum(points), row.match_score, delta=.03)

    def test_unknown_prices_render_without_fake_metrics(self):
        app = self.app()
        app.button(key='nav_Market Insights').click().run()
        app.number_input(key='market_budget').set_value(1).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[1].value, 'Not reported')
        self.assertEqual(app.metric[3].value, '0')
        self.assertTrue(any('No reported prices' in item.value for item in app.info))

    def test_navigation_and_original_listing_links(self):
        app = self.app()
        for title in ['Personalized Picks', 'Market Insights', 'Behind the Data', 'Discover Stays']:
            app.button(key='nav_' + title).click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.button(key='nav_' + title).proto.type, 'primary')
        links = app.get('link_button')
        self.assertEqual(len(links), 9)
        for link in links:
            self.assertRegex(link.proto.url, r'^https://www\.airbnb\.com/rooms/\d+$')


if __name__ == '__main__':
    unittest.main()

class ExplorationTests(unittest.TestCase):
    def test_compare_and_filter_cleanup(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()
        data = pd.read_csv(ROOT / 'data/processed/listings.csv.gz')
        from src.recommend import filter_listings
        eligible = filter_listings(data, 250, guests=2).sort_values(['price', 'id'])
        selected = eligible.id.head(3).tolist()
        app.multiselect(key='discover_compare').set_value(selected).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 3)
        self.assertEqual(app.multiselect(key='discover_compare').proto.max_selections, 3)
        self.assertEqual(app.metric[0].value, f'${eligible.price.iloc[0]:,.2f}')
        app.number_input(key='discover_budget').set_value(1).run()
        self.assertEqual(len(app.exception), 0)
        app.button(key='discover_reset').click().run()
        self.assertEqual(app.number_input(key='discover_budget').value, 250)
        self.assertEqual(app.multiselect(key='discover_compare').value, [])

    def test_pagination_reset_and_recommendation_comparison(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()
        app.number_input(key='discover_page').set_value(2).run()
        app.number_input(key='discover_guests').set_value(3).run()
        self.assertEqual(app.number_input(key='discover_page').value, 1)
        app.button(key='nav_Personalized Picks').click().run()
        data = pd.read_csv(ROOT / 'data/processed/listings.csv.gz')
        top = recommend(data, 250, guests=2)
        app.multiselect(key='picks_compare').set_value(top.id.head(2).tolist()).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[1].value, f'{top.match_score.iloc[0]:.1f}')
        app.multiselect(key='preferred_amenities').set_value(['Wi-Fi']).run()
        app.button(key='picks_reset').click().run()
        self.assertEqual(app.multiselect(key='preferred_amenities').value, [])
        self.assertEqual(len(app.exception), 0)

class PaginationWarningTests(unittest.TestCase):
    def test_no_duplicate_default_and_pagination_survives_navigation(self):
        import ast
        tree = ast.parse((ROOT / 'app.py').read_text())
        widgets = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                   and any(k.arg == 'key' and isinstance(k.value, ast.Constant)
                           and k.value.value == 'discover_page' for k in node.keywords)]
        self.assertEqual(len(widgets), 1)
        default = next(k.value for k in widgets[0].keywords if k.arg == 'value')
        self.assertIsNone(default.value)
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()
        self.assertEqual(app.number_input(key='discover_page').value, 1)
        app.number_input(key='discover_page').set_value(2).run()
        self.assertEqual(app.number_input(key='discover_page').value, 2)
        app.multiselect(key='discover_compare').set_value([]).run()
        self.assertEqual(app.number_input(key='discover_page').value, 2)
        app.button(key='discover_reset').click().run()
        self.assertEqual(app.number_input(key='discover_page').value, 1)
        app.button(key='nav_Market Insights').click().run()
        app.button(key='nav_Discover Stays').click().run()
        self.assertEqual(app.number_input(key='discover_page').value, 1)
        self.assertFalse(any('Session State API' in w.value for w in app.warning))
        self.assertEqual(len(app.exception), 0)

class MapTitleTests(unittest.TestCase):
    def test_map_has_explicit_title_and_preserves_map_settings(self):
        import json
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()
        app.button(key='nav_Market Insights').click().run()
        self.assertEqual(len(app.exception), 0)
        figures = [json.loads(chart.proto.spec) for chart in app.get('plotly_chart')]
        maps = [fig for fig in figures if any(t['type'] == 'scattermap' for t in fig['data'])]
        self.assertEqual(len(maps), 1)
        figure = maps[0]
        self.assertEqual(figure['layout']['title']['text'], 'Washington, D.C. listing locations')
        self.assertEqual(figure['layout']['map']['style'], 'open-street-map')
        trace = figure['data'][0]
        self.assertIn('lat', trace)
        self.assertIn('lon', trace)
        for label in ['Neighborhood', 'Nightly price (USD)', 'Review / 5', 'Guest capacity']:
            self.assertIn(label, trace['hovertemplate'])
        self.assertNotIn('undefined', json.dumps(figure['layout']['title']))
