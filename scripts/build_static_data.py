from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import apple_summary, city_production_correlation, city_summary  # noqa: E402
from src.data_loader import CITY_FILES, load_all_data  # noqa: E402
from src.config import CITY_COORDS  # noqa: E402


def main() -> None:
    temperature, apple = load_all_data(ROOT / "data")
    cities = {}
    for city in CITY_FILES:
        frame = temperature[temperature["도시"] == city].sort_values("연도")
        cities[city] = {
            "records": frame[["연도", "연평균기온", "평균최저기온", "평균최고기온"]].to_dict("records"),
            "summary": city_summary(frame),
            "correlation": city_production_correlation(frame, apple),
            "coords": CITY_COORDS[city],
        }
    payload = {
        "period": {"start": 2012, "end": 2024, "count": 13},
        "cities": cities,
        "apple": {
            "records": apple.to_dict("records"),
            "summary": apple_summary(apple),
            "scope": "경상북도 전체",
        },
        "meta": {
            "generated_from": [*CITY_FILES.values(), "data_appleproduce.csv"],
            "warning": "상관관계는 인과관계를 뜻하지 않습니다.",
        },
    }
    output = ROOT / "dist" / "data" / "analysis.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
