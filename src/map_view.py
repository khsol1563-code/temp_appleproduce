from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

import folium
import pandas as pd
from branca.colormap import LinearColormap

from .config import CITY_COORDS

GEOJSON_URL = (
    "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/"
    "kostat/2018/json/skorea-municipalities-2018-geo.json"
)


def load_boundary(cache_path: Path | None = None):
    if cache_path and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    try:
        with urlopen(GEOJSON_URL, timeout=8) as response:
            return json.load(response)
    except Exception:
        return None


def create_climate_map(temperature: pd.DataFrame, year: int, cache_path: Path | None = None):
    map_object = folium.Map(location=[36.35, 128.65], zoom_start=8, tiles="CartoDB positron")
    boundary = load_boundary(cache_path)
    if boundary:
        folium.GeoJson(
            boundary,
            name="대한민국 시군 경계",
            style_function=lambda _: {"color": "#6b7280", "weight": 0.7, "fillOpacity": 0.02},
        ).add_to(map_object)
    color_scale = LinearColormap(["#4da3d9", "#f7c873", "#df4b3f"], vmin=-1, vmax=3)
    color_scale.caption = "2012년 대비 연평균기온 변화량 (°C)"
    color_scale.add_to(map_object)
    for city, coords in CITY_COORDS.items():
        city_frame = temperature[temperature["도시"] == city].set_index("연도")
        selected = city_frame.loc[year]
        base = city_frame.loc[2012]
        change = float(selected["연평균기온"] - base["연평균기온"])
        popup = (
            f"<b>{city}</b><br>{year}년 연평균기온: {selected['연평균기온']:.1f}°C"
            f"<br>평균최저기온: {selected['평균최저기온']:.1f}°C"
            f"<br>평균최고기온: {selected['평균최고기온']:.1f}°C"
            f"<br>2012년 대비: {change:+.1f}°C<br><small>{coords['note']}</small>"
        )
        folium.CircleMarker(
            location=[coords["lat"], coords["lon"]],
            radius=max(10, float(selected["연평균기온"]) * 1.05),
            color="#ffffff", weight=2, fill=True, fill_color=color_scale(change), fill_opacity=0.9,
            tooltip=f"{city} {selected['연평균기온']:.1f}°C", popup=folium.Popup(popup, max_width=320),
        ).add_to(map_object)
    folium.LayerControl(collapsed=True).add_to(map_object)
    return map_object

