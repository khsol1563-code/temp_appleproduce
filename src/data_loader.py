from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pandas as pd


ENCODINGS = ("utf-8-sig", "cp949", "euc-kr", "utf-8")
CITY_FILES = {
    "영주": "data_temp_yeongju.csv",
    "문경": "data_temp_mungeong.csv",
    "영천": "data_temp_yeongcheon.csv",
}


class DataFormatError(ValueError):
    """사용자가 이해할 수 있는 데이터 형식 오류."""


def read_text_safely(path: Path) -> str:
    errors: list[str] = []
    for encoding in ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise DataFormatError(f"{path.name}의 문자 인코딩을 읽지 못했습니다. " + " | ".join(errors))


def load_temperature_csv(path: Path, city: str) -> pd.DataFrame:
    text = read_text_safely(path)
    cleaned = [line.strip().lstrip("\t").replace("\r", "") for line in text.splitlines()]
    header_index = next(
        (index for index, line in enumerate(cleaned) if line.startswith("년,") and "평균기온" in line),
        None,
    )
    if header_index is None:
        raise DataFormatError(f"{path.name}에서 기온 데이터 머리글을 찾지 못했습니다.")

    useful = [line for line in cleaned[header_index:] if line and not line.startswith(",")]
    frame = pd.read_csv(StringIO("\n".join(useful)))
    frame.columns = [str(column).strip() for column in frame.columns]
    required = ["년", "지점", "평균기온(℃)", "평균최저기온(℃)", "평균최고기온(℃)"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise DataFormatError(f"{path.name}에 필요한 열이 없습니다: {', '.join(missing)}")

    frame = frame[required].copy()
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["년"]).copy()
    frame["년"] = frame["년"].astype(int)
    frame["도시"] = city
    frame = frame.rename(
        columns={
            "년": "연도",
            "평균기온(℃)": "연평균기온",
            "평균최저기온(℃)": "평균최저기온",
            "평균최고기온(℃)": "평균최고기온",
        }
    )
    if frame["연도"].duplicated().any():
        duplicate_years = frame.loc[frame["연도"].duplicated(), "연도"].tolist()
        raise DataFormatError(f"{path.name}에 중복 연도가 있습니다: {duplicate_years}")
    numeric = ["연평균기온", "평균최저기온", "평균최고기온"]
    if frame[numeric].isna().any().any():
        raise DataFormatError(f"{path.name}에 비어 있거나 숫자가 아닌 기온 값이 있습니다.")
    return frame.sort_values("연도").reset_index(drop=True)


def load_apple_csv(path: Path) -> pd.DataFrame:
    text = read_text_safely(path)
    rows = list(csv.reader(StringIO(text)))
    if len(rows) < 3:
        raise DataFormatError(f"{path.name}의 행 수가 부족합니다.")
    years_row, values_row = rows[0], rows[2]
    records: list[dict[str, float | int]] = []
    for index in range(1, min(len(years_row), len(values_row)), 3):
        try:
            year = int(str(years_row[index]).strip())
            area = float(str(values_row[index]).replace(",", "").strip())
            yield_10a = float(str(values_row[index + 1]).replace(",", "").strip())
            production = float(str(values_row[index + 2]).replace(",", "").strip())
        except (ValueError, IndexError):
            continue
        records.append(
            {
                "연도": year,
                "재배면적_ha": area,
                "10a당생산량_kg": yield_10a,
                "총생산량_톤": production,
            }
        )
    frame = pd.DataFrame(records).sort_values("연도").reset_index(drop=True)
    if frame.empty:
        raise DataFormatError(f"{path.name}에서 사과 데이터를 읽지 못했습니다.")
    if frame["연도"].duplicated().any():
        raise DataFormatError(f"{path.name}에 중복 연도가 있습니다.")
    return frame


def load_all_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    temperatures = []
    for city, filename in CITY_FILES.items():
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"필수 데이터 파일이 없습니다: {path}")
        temperatures.append(load_temperature_csv(path, city))
    apple_path = data_dir / "data_appleproduce.csv"
    if not apple_path.exists():
        raise FileNotFoundError(f"필수 데이터 파일이 없습니다: {apple_path}")
    temperature = pd.concat(temperatures, ignore_index=True)
    apple = load_apple_csv(apple_path)
    expected = set(range(2012, 2026))
    for city in CITY_FILES:
        actual = set(temperature.loc[temperature["도시"] == city, "연도"])
        if actual != expected:
            raise DataFormatError(f"{city} 기온 자료의 연도가 2012~2025와 일치하지 않습니다.")
    if set(apple["연도"]) != expected:
        raise DataFormatError("경북 사과 자료의 연도가 2012~2025와 일치하지 않습니다.")
    return temperature, apple

