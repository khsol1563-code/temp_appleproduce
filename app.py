from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.analysis import (
    apple_summary,
    city_production_correlation,
    city_summary,
    correlation_label,
)
from src.charts import (
    all_city_chart,
    change_bar_chart,
    city_metric_chart,
    configure_korean_font,
    dual_axis_chart,
    scatter_chart,
    temperature_bundle_chart,
)
from src.config import CITY_COORDS
from src.content import ACHIEVEMENTS, CAUSATION_NOTE, SOLUTIONS, SUBTITLE, TITLE
from src.data_loader import CITY_FILES, DataFormatError, load_all_data
from src.map_view import create_climate_map


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
GEOJSON_CACHE = ROOT / "data" / "skorea-municipalities-2018-geo.json"

st.set_page_config(page_title=f"{TITLE} | 경북 기후·사과 탐구", page_icon="🍎", layout="wide")
configure_korean_font()

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg,#fffdf7 0%,#f5fbf8 100%);}
    .hero {padding:2rem 2.2rem;border-radius:24px;background:linear-gradient(125deg,#b92f2f,#e85b3f 55%,#f5a742);color:white;margin-bottom:1rem;box-shadow:0 14px 35px rgba(122,35,35,.18)}
    .hero h1 {margin:0;font-size:2.65rem}.hero p {font-size:1.14rem;margin:.55rem 0 0;opacity:.95}
    .note {padding:1rem 1.2rem;border-left:5px solid #2f8f6b;background:#edf8f2;border-radius:12px;color:#173d2f}
    .scope {padding:.8rem 1rem;background:#fff4d7;border:1px solid #f0cd74;border-radius:12px;color:#5c4300}
    div[data-testid="stMetric"] {background:white;border:1px solid #e9e2d7;border-radius:16px;padding:1rem;box-shadow:0 8px 22px rgba(43,55,48,.06)}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data():
    return load_all_data(DATA_DIR)


try:
    temperature, apple = get_data()
except (FileNotFoundError, DataFormatError) as exc:
    st.error(f"데이터를 준비하지 못했습니다: {exc}")
    st.stop()

st.markdown(
    f'<div class="hero"><div style="font-size:2rem">🍎</div><h1>{TITLE}</h1><p>{SUBTITLE}</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("탐구 조건")
    selected_city = st.selectbox("도시", list(CITY_FILES), index=0)
    selected_metric = st.selectbox("기온 지표", ["연평균기온", "평균최저기온", "평균최고기온"])
    year_range = st.slider("분석 기간", 2012, 2024, (2012, 2024))
    show_trend = st.toggle("추세선 보기", value=True)
    show_table = st.toggle("데이터 표 보기", value=False)
    st.caption("농업 자료는 세 도시별 값이 아니라 경상북도 전체 자료입니다.")

filtered_temperature = temperature[temperature["연도"].between(*year_range)]
city_frame = filtered_temperature[filtered_temperature["도시"] == selected_city].copy()
full_city_frame = temperature[temperature["도시"] == selected_city].copy()
filtered_apple = apple[apple["연도"].between(*year_range)].copy()

tabs = st.tabs(["이야기 시작", "기온 변화", "사과와 비교", "기후 지도", "생각·토론"])

with tabs[0]:
    st.subheader("대구 사과는 왜 경북 북부로 이동했을까요?")
    st.write("그래프와 지도를 직접 움직이며 기온과 경북 사과 재배의 변화를 탐구해 봅시다.")
    col1, col2, col3 = st.columns(3)
    col1.metric("데이터 기간", "2012~2024", "13년")
    col2.metric("기온 관측 지역", "3곳", "영주·문경·영천")
    col3.metric("농업 자료 범위", "경상북도 전체", "시군별 자료 아님")
    st.markdown('<div class="scope"><b>먼저 예상해 보세요.</b><br>기온이 높아지면 경북의 사과 재배면적은 늘어날까요, 줄어들까요?</div>', unsafe_allow_html=True)
    st.markdown("### 우리가 해결할 다섯 가지 질문")
    questions = [
        "세 도시의 기온은 2012년부터 2024년까지 어떻게 변했을까요?",
        "같은 기간 경북 사과 재배면적과 총생산량은 어떻게 변했을까요?",
        "기온과 사과 생산량 사이에는 어떤 관계가 나타날까요?",
        "이 결과만으로 기온 상승이 직접 원인이라고 말할 수 있을까요?",
        "지역사회와 농가는 어떤 준비를 할 수 있을까요?",
    ]
    for index, question in enumerate(questions, 1):
        st.markdown(f"**{index}.** {question}")
    with st.expander("낱말 도움말"):
        st.write("**연평균기온**: 한 해 동안 관측한 기온의 평균값입니다.")
        st.write("**총생산량**: 한 해 동안 생산한 사과의 전체 무게입니다.")
        st.write("**상관관계**: 두 값이 함께 변하는 경향을 숫자로 나타낸 것입니다.")

with tabs[1]:
    summary = city_summary(city_frame)
    st.caption(f"현재 선택: {selected_city} · {year_range[0]}~{year_range[1]}년 · {selected_metric}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("처음 연평균기온", f"{summary['start_temp']:.1f}°C")
    c2.metric("마지막 연평균기온", f"{summary['end_temp']:.1f}°C", f"{summary['change']:+.1f}°C")
    c3.metric("10년당 추세", f"{summary['change_per_decade']:+.2f}°C")
    c4.metric("가장 더운 해", f"{summary['hottest_year']}년", f"{summary['hottest_temp']:.1f}°C")
    st.pyplot(city_metric_chart(city_frame, selected_city, selected_metric, show_trend), use_container_width=True)
    st.info(f"{selected_city}의 선택 기간 {selected_metric} 흐름입니다. 점선은 전체 흐름을 단순하게 나타낸 선형 추세선입니다.")
    left, right = st.columns(2)
    with left:
        st.pyplot(all_city_chart(filtered_temperature), use_container_width=True)
    with right:
        st.pyplot(change_bar_chart(temperature), use_container_width=True)
    st.pyplot(temperature_bundle_chart(city_frame, selected_city), use_container_width=True)
    if show_table:
        st.dataframe(city_frame, hide_index=True, use_container_width=True)

with tabs[2]:
    apple_stats = apple_summary(filtered_apple)
    correlation = city_production_correlation(city_frame, filtered_apple)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{selected_city} 기온 변화", f"{summary['change']:+.1f}°C")
    c2.metric("경북 재배면적 변화", f"{apple_stats['area_change_pct']:+.1f}%")
    c3.metric("경북 총생산량 변화", f"{apple_stats['production_change_pct']:+.1f}%")
    c4.metric("기온·총생산량 상관계수", f"{correlation:.2f}", correlation_label(correlation))
    comparison_metric = st.radio("비교할 농업 지표", ["재배면적", "총생산량", "10a당 생산량"], horizontal=True)
    st.pyplot(dual_axis_chart(city_frame, filtered_apple, selected_city, comparison_metric), use_container_width=True)
    left, right = st.columns([1.3, 1])
    with left:
        st.pyplot(scatter_chart(city_frame, filtered_apple, selected_city), use_container_width=True)
    with right:
        st.markdown("#### 도시별 상관계수")
        corr_table = []
        for city in CITY_FILES:
            frame = filtered_temperature[filtered_temperature["도시"] == city]
            value = city_production_correlation(frame, filtered_apple)
            corr_table.append({"도시": city, "상관계수": value, "해석": correlation_label(value)})
        corr_df = pd.DataFrame(corr_table).set_index("도시")
        st.bar_chart(corr_df["상관계수"], color="#2f8f6b", horizontal=True)
        st.dataframe(corr_df.style.format({"상관계수": "{:.2f}"}), use_container_width=True)
        st.markdown(f'<div class="note">{CAUSATION_NOTE}</div>', unsafe_allow_html=True)
    if show_table:
        st.dataframe(filtered_apple, hide_index=True, use_container_width=True)

with tabs[3]:
    map_year = st.slider("지도에서 살펴볼 연도", 2012, 2024, 2024, key="map_year")
    st.caption(f"{map_year}년 도시별 기온 · 원의 크기는 연평균기온, 색은 2012년 대비 변화량을 나타냅니다.")
    climate_map = create_climate_map(temperature, map_year, GEOJSON_CACHE)
    st_folium(climate_map, height=570, use_container_width=True, returned_objects=[])
    cols = st.columns(3)
    for column, city in zip(cols, CITY_COORDS):
        row = temperature[(temperature["도시"] == city) & (temperature["연도"] == map_year)].iloc[0]
        base = temperature[(temperature["도시"] == city) & (temperature["연도"] == 2012)].iloc[0]
        column.metric(city, f"{row['연평균기온']:.1f}°C", f"2012년 대비 {row['연평균기온'] - base['연평균기온']:+.1f}°C")
        column.caption(CITY_COORDS[city]["note"])
    st.markdown('<div class="scope">현재 지도는 세 도시의 기온 변화를 나타냅니다. 지역별 사과 재배면적 자료를 추가하면 미래에는 사과 산지 이동도 함께 비교할 수 있습니다.</div>', unsafe_allow_html=True)

with tabs[4]:
    st.subheader("관찰하고, 판단하고, 해결책을 제안해 보세요")
    st.markdown("#### 활동 1. 그래프 관찰")
    st.write("• 가장 기온이 많이 오른 도시는 어디인가요?")
    st.write("• 경북 사과 재배면적은 어떻게 변했나요?")
    st.write("• 총생산량이 매년 일정하게 감소하지 않는 이유는 무엇일까요?")
    st.markdown("#### 활동 2. 자료 해석")
    answer = st.radio(
        "자료를 가장 정확하게 해석한 문장을 고르세요.",
        [
            "기온이 상승할수록 사과 생산량은 반드시 감소한다.",
            "두 자료에는 감소 경향이 있지만 기온만으로 모든 변화를 설명할 수 없다.",
            "상관계수가 음수이면 기온이 생산량 감소의 유일한 원인이다.",
        ],
        index=None,
    )
    if st.button("정답 확인", type="primary"):
        if answer == "두 자료에는 감소 경향이 있지만 기온만으로 모든 변화를 설명할 수 없다.":
            st.success("정답입니다! 자료의 경향과 인과관계를 구분했어요.")
        elif answer:
            st.warning("다시 생각해 보세요. 상관관계만으로 직접 원인을 확정할 수는 없습니다.")
        else:
            st.info("먼저 문장을 하나 선택해 주세요.")
    st.markdown("#### 활동 3. 지역사회의 해결책")
    solution = st.selectbox("가장 중요하다고 생각하는 해결책", SOLUTIONS)
    reason = st.text_area("그 해결책을 고른 이유를 써 보세요.", placeholder="그래프나 지도에서 찾은 근거를 함께 적어 보세요.")
    if st.button("나의 제안 정리"):
        if reason.strip():
            st.success(f"나의 제안: ‘{solution}’이 중요합니다. 이유: {reason.strip()}")
        else:
            st.info("이유를 먼저 적어 주세요.")
    with st.expander("교사용 수업 활용 안내와 교육과정 연계"):
        for item in ACHIEVEMENTS:
            st.write(f"• {item}")
        st.markdown("**도입** 예상 말하기 → **전개** 그래프·지도 탐색 → **정리** 사실과 추측 구분 → **평가** 근거를 들어 대응 방안 제안")

st.divider()
st.caption("자료 범위: 기온은 영주·문경·영천, 농업은 경상북도 전체 · 분석 기간 2012~2024년 · 장기 미래 예측에는 추가 자료가 필요합니다.")

