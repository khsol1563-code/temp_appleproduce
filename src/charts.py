from __future__ import annotations

import platform

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

from .analysis import join_city_apple


COLORS = {"영주": "#d84a3a", "문경": "#2f8f6b", "영천": "#3478b8"}


def configure_korean_font() -> None:
    candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]
    available = {item.name for item in font_manager.fontManager.ttflist}
    selected = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["font.family"] = selected
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid", font=selected)


def _finalize(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel("연도")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=":", alpha=0.45)


def city_metric_chart(city_frame: pd.DataFrame, city: str, metric: str, trend: bool):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(city_frame["연도"], city_frame[metric], marker="o", linewidth=2.8,
            color=COLORS[city], label=metric)
    if trend:
        slope, intercept = np.polyfit(city_frame["연도"], city_frame[metric], 1)
        ax.plot(city_frame["연도"], slope * city_frame["연도"] + intercept,
                linestyle="--", color="#495057", label="선형 추세선")
    _finalize(ax, f"{city} {metric} 변화", "기온 (°C)")
    ax.legend()
    fig.tight_layout()
    return fig


def all_city_chart(temperature: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    for city, frame in temperature.groupby("도시"):
        ax.plot(frame["연도"], frame["연평균기온"], marker="o", linewidth=2.3,
                color=COLORS[city], label=city)
    _finalize(ax, "세 도시의 연평균기온 비교", "연평균기온 (°C)")
    ax.legend(ncol=3)
    fig.tight_layout()
    return fig


def temperature_bundle_chart(city_frame: pd.DataFrame, city: str):
    fig, ax = plt.subplots(figsize=(10, 5))
    styles = [("연평균기온", "#e63946", "-", "o"), ("평균최저기온", "#457b9d", "--", "s"),
              ("평균최고기온", "#f4a261", "--", "^")]
    for metric, color, line, marker in styles:
        ax.plot(city_frame["연도"], city_frame[metric], color=color, linestyle=line,
                marker=marker, linewidth=2.2, label=metric)
    _finalize(ax, f"{city} 연도별 기온 변화", "기온 (°C)")
    ax.legend(ncol=3)
    fig.tight_layout()
    return fig


def change_bar_chart(temperature: pd.DataFrame):
    values = []
    for city, frame in temperature.groupby("도시"):
        ordered = frame.sort_values("연도")
        values.append((city, ordered.iloc[-1]["연평균기온"] - ordered.iloc[0]["연평균기온"]))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cities = [item[0] for item in values]
    changes = [item[1] for item in values]
    bars = ax.bar(cities, changes, color=[COLORS[city] for city in cities], width=0.6)
    ax.bar_label(bars, fmt="+%.1f°C", padding=4, fontweight="bold")
    ax.set_title("2012년 대비 2025년 연평균기온 변화", fontweight="bold")
    ax.set_ylabel("변화량 (°C)")
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    fig.tight_layout()
    return fig


def dual_axis_chart(city_frame: pd.DataFrame, apple: pd.DataFrame, city: str, metric: str):
    joined = join_city_apple(city_frame, apple)
    column, label, color = {
        "재배면적": ("재배면적_ha", "경북 사과 재배면적 (ha)", "#a8dadc"),
        "총생산량": ("총생산량_톤", "경북 사과 총생산량 (톤)", "#2a9d8f"),
        "10a당 생산량": ("10a당생산량_kg", "경북 사과 10a당 생산량 (kg)", "#6a994e"),
    }[metric]
    fig, ax = plt.subplots(figsize=(10, 5))
    if metric == "재배면적":
        ax.bar(joined["연도"], joined[column], color=color, alpha=0.8, label=label)
    else:
        ax.plot(joined["연도"], joined[column], color=color, marker="s", linewidth=2.6, label=label)
    ax.set_ylabel(label, color=color, fontweight="bold")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax2 = ax.twinx()
    ax2.plot(joined["연도"], joined["연평균기온"], color="#e63946", marker="o",
             linewidth=2.5, linestyle="--", label=f"{city} 연평균기온 (°C)")
    ax2.set_ylabel("연평균기온 (°C)", color="#e63946", fontweight="bold")
    ax.set_title(f"{city} 연평균기온과 {label} 비교", fontweight="bold", pad=12)
    ax.set_xlabel("연도")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="best")
    ax.grid(True, linestyle=":", alpha=0.4)
    fig.tight_layout()
    return fig


def scatter_chart(city_frame: pd.DataFrame, apple: pd.DataFrame, city: str):
    joined = join_city_apple(city_frame, apple)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.regplot(data=joined, x="연평균기온", y="총생산량_톤", ax=ax,
                scatter_kws={"s": 65, "color": COLORS[city]},
                line_kws={"color": "#333333", "linestyle": "--"})
    for _, row in joined.iterrows():
        ax.annotate(str(int(row["연도"])), (row["연평균기온"], row["총생산량_톤"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_title(f"{city} 기온과 경북 사과 총생산량의 관계", fontweight="bold")
    ax.set_xlabel("연평균기온 (°C)")
    ax.set_ylabel("경북 사과 총생산량 (톤)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    fig.tight_layout()
    return fig

