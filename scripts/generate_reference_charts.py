from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_loader import load_all_data  # noqa: E402


CITY_FILE_NAMES = {
    "영주": ("tempchange_yeongju.jpg", "appleproducechange_yeongju.jpg"),
    "문경": ("tempchange_mun.jpeg", "appleproducechange_mun.jpeg"),
    "영천": ("tempchange_yeongchun.jpeg", "appleproducechange_yeongchun.jpeg"),
}


def configure_font() -> None:
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def save_both(fig, filename: str) -> None:
    for folder in (ROOT / "assets" / "reference", ROOT / "dist" / "assets"):
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / filename, dpi=150, bbox_inches="tight", facecolor="white")


def temperature_chart(city: str, frame, filename: str) -> None:
    years = frame["연도"]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(years, frame["연평균기온"], color="#e63946", marker="o", linewidth=3, label="연평균 기온 (°C)")
    ax.plot(years, frame["평균최저기온"], color="#457b9d", marker="s", linestyle="--", linewidth=2.2, label="평균 최저기온 (°C)")
    ax.plot(years, frame["평균최고기온"], color="#f4a261", marker="^", linestyle="--", linewidth=2.2, label="평균 최고기온 (°C)")
    ax.set_title(f"{city}시 연도별 기온 변화 추이 (2012~2025년)", fontsize=23, fontweight="bold", pad=22)
    ax.set_xlabel("연도 (년)", fontsize=15)
    ax.set_ylabel("기온 (°C)", fontsize=15)
    ax.set_xticks(years)
    ax.grid(True, linestyle=":", alpha=.45)
    ax.legend(loc="upper left", fontsize=13)
    first, last = frame.iloc[0], frame.iloc[-1]
    ax.annotate(f"{first['연평균기온']:.1f}°C", (first["연도"], first["연평균기온"]), xytext=(-18, 14), textcoords="offset points", color="#e63946", fontsize=12, fontweight="bold")
    ax.annotate(f"{last['연평균기온']:.1f}°C", (last["연도"], last["연평균기온"]), xytext=(-20, 14), textcoords="offset points", color="#e63946", fontsize=12, fontweight="bold")
    fig.tight_layout()
    save_both(fig, filename)
    plt.close(fig)


def comparison_chart(city: str, frame, apple, filename: str) -> None:
    years = apple["연도"]
    corr = np.corrcoef(frame["연평균기온"], apple["총생산량_톤"])[0, 1]
    fig, (left, right) = plt.subplots(1, 2, figsize=(17, 6.5))

    left.bar(years, apple["재배면적_ha"], color="#acd9db", alpha=.88, label="경북 사과 재배면적 (ha)")
    left_t = left.twinx()
    left_t.plot(years, frame["연평균기온"], color="#e63946", marker="o", linewidth=2.8, label=f"{city} 연평균 기온 (°C)")
    left.set_title(f"{city} 기온 상승과 경북 사과 재배면적 변화 (2012~2025)", fontsize=17, fontweight="bold")
    left.set_ylabel("사과 재배면적 (ha)", fontweight="bold")
    left_t.set_ylabel("연평균 기온 (°C)", color="#e63946", fontweight="bold")
    lines, labels = left.get_legend_handles_labels()
    lines2, labels2 = left_t.get_legend_handles_labels()
    left.legend(lines + lines2, labels + labels2, loc="upper center")

    right.plot(years, apple["총생산량_톤"], color="#2a9d8f", marker="s", linewidth=2.8, label="경북 사과 총생산량 (톤)")
    right_t = right.twinx()
    right_t.plot(years, frame["연평균기온"], color="#e63946", marker="o", linestyle="--", linewidth=2.8, label=f"{city} 연평균 기온 (°C)")
    right.set_title(f"{city} 기온과 경북 사과 총생산량 추이 비교 (r = {corr:.2f})", fontsize=17, fontweight="bold")
    right.set_ylabel("사과 총생산량 (톤)", color="#2a9d8f", fontweight="bold")
    right_t.set_ylabel("연평균 기온 (°C)", color="#e63946", fontweight="bold")
    lines, labels = right.get_legend_handles_labels()
    lines2, labels2 = right_t.get_legend_handles_labels()
    right.legend(lines + lines2, labels + labels2, loc="upper right")

    for ax in (left, right):
        ax.set_xticks(years)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, linestyle=":", alpha=.35)
        ax.set_xlabel("연도 (년)")
    fig.tight_layout()
    save_both(fig, filename)
    plt.close(fig)


def main() -> None:
    configure_font()
    temperature, apple = load_all_data(ROOT / "data")
    for city, (temp_name, compare_name) in CITY_FILE_NAMES.items():
        frame = temperature[temperature["도시"] == city].sort_values("연도")
        temperature_chart(city, frame, temp_name)
        comparison_chart(city, frame, apple, compare_name)


if __name__ == "__main__":
    main()
