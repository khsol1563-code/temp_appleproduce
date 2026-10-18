from pathlib import Path
import unittest

from src.analysis import apple_summary, city_production_correlation, city_summary, join_city_apple
from src.data_loader import load_all_data


ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_analysis_outputs(self):
        temperature, apple = load_all_data(ROOT / "data")
        summary = apple_summary(apple)
        self.assertEqual(summary["start_production"], 320078)
        self.assertEqual(summary["end_production"], 270105)
        self.assertAlmostEqual(summary["area_change_pct"], -21.5888, places=3)
        for city in ("영주", "문경", "영천"):
            frame = temperature[temperature["도시"] == city]
            self.assertEqual(len(join_city_apple(frame, apple)), 14)
            correlation = city_production_correlation(frame, apple)
            self.assertTrue(-1 <= correlation <= 1)
            self.assertGreater(city_summary(frame)["change"], 0)


if __name__ == "__main__":
    unittest.main()

