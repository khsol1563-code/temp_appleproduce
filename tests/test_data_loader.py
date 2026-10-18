from pathlib import Path
import unittest

from src.data_loader import DataFormatError, load_all_data, load_temperature_csv


ROOT = Path(__file__).resolve().parents[1]


class DataLoaderTests(unittest.TestCase):
    def test_all_years_and_key_values(self):
        temperature, apple = load_all_data(ROOT / "data")
        self.assertEqual(len(apple), 14)
        self.assertEqual(set(apple["연도"]), set(range(2012, 2026)))
        expected = {"영주": (11.2, 13.2), "문경": (11.5, 13.8), "영천": (12.3, 14.9)}
        for city, (start, end) in expected.items():
            frame = temperature[temperature["도시"] == city].set_index("연도")
            self.assertEqual(len(frame), 14)
            self.assertAlmostEqual(frame.loc[2012, "연평균기온"], start)
            self.assertAlmostEqual(frame.loc[2025, "연평균기온"], end)
        apples = apple.set_index("연도")
        self.assertEqual(apples.loc[2012, "재배면적_ha"], 15332)
        self.assertEqual(apples.loc[2025, "재배면적_ha"], 12022)
        self.assertEqual(apples.loc[2015, "총생산량_톤"], 332627)

    def test_missing_temperature_value_is_reported(self):
        path = ROOT / "tests" / "_bad_temperature_fixture.csv"
        try:
            path.write_text("년,지점,평균기온(℃),평균최저기온(℃),평균최고기온(℃)\n2012,1,,5,15", encoding="utf-8")
            with self.assertRaises(DataFormatError):
                load_temperature_csv(path, "시험")
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

