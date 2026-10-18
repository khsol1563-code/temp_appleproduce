from __future__ import annotations

import numpy as np
import pandas as pd


def city_summary(city_frame: pd.DataFrame) -> dict[str, float | int]:
    ordered = city_frame.sort_values("연도")
    start = ordered.iloc[0]
    end = ordered.iloc[-1]
    slope, intercept = np.polyfit(ordered["연도"], ordered["연평균기온"], 1)
    hottest = ordered.loc[ordered["연평균기온"].idxmax()]
    coldest = ordered.loc[ordered["연평균기온"].idxmin()]
    return {
        "start_year": int(start["연도"]),
        "end_year": int(end["연도"]),
        "start_temp": float(start["연평균기온"]),
        "end_temp": float(end["연평균기온"]),
        "change": float(end["연평균기온"] - start["연평균기온"]),
        "period_average": float(ordered["연평균기온"].mean()),
        "slope_per_year": float(slope),
        "change_per_decade": float(slope * 10),
        "intercept": float(intercept),
        "hottest_year": int(hottest["연도"]),
        "hottest_temp": float(hottest["연평균기온"]),
        "coldest_year": int(coldest["연도"]),
        "coldest_temp": float(coldest["연평균기온"]),
    }


def apple_summary(apple: pd.DataFrame) -> dict[str, float | int]:
    ordered = apple.sort_values("연도")
    start = ordered.iloc[0]
    end = ordered.iloc[-1]
    max_row = ordered.loc[ordered["총생산량_톤"].idxmax()]
    min_row = ordered.loc[ordered["총생산량_톤"].idxmin()]
    return {
        "start_area": float(start["재배면적_ha"]),
        "end_area": float(end["재배면적_ha"]),
        "area_change": float(end["재배면적_ha"] - start["재배면적_ha"]),
        "area_change_pct": float((end["재배면적_ha"] / start["재배면적_ha"] - 1) * 100),
        "start_production": float(start["총생산량_톤"]),
        "end_production": float(end["총생산량_톤"]),
        "production_change": float(end["총생산량_톤"] - start["총생산량_톤"]),
        "production_change_pct": float((end["총생산량_톤"] / start["총생산량_톤"] - 1) * 100),
        "start_yield": float(start["10a당생산량_kg"]),
        "end_yield": float(end["10a당생산량_kg"]),
        "yield_change_pct": float((end["10a당생산량_kg"] / start["10a당생산량_kg"] - 1) * 100),
        "max_year": int(max_row["연도"]),
        "max_production": float(max_row["총생산량_톤"]),
        "min_year": int(min_row["연도"]),
        "min_production": float(min_row["총생산량_톤"]),
    }


def join_city_apple(city_frame: pd.DataFrame, apple: pd.DataFrame) -> pd.DataFrame:
    return city_frame.merge(apple, on="연도", how="inner", validate="one_to_one")


def city_production_correlation(city_frame: pd.DataFrame, apple: pd.DataFrame) -> float:
    joined = join_city_apple(city_frame, apple)
    return float(joined["연평균기온"].corr(joined["총생산량_톤"]))


def correlation_label(value: float) -> str:
    strength = abs(value)
    if strength < 0.2:
        degree = "거의 뚜렷하지 않은"
    elif strength < 0.4:
        degree = "약한"
    elif strength < 0.7:
        degree = "중간 정도의"
    else:
        degree = "강한"
    direction = "음의" if value < 0 else "양의"
    return f"{degree} {direction} 상관 경향"

