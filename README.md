# 사과가 사라진다고?

영주·문경·영천의 2012~2025년 기온과 경상북도 전체 사과 재배면적·생산량을 비교하는 초등 사회·과학 데이터 리터러시 웹앱입니다.

## 구현 구성

- `app.py`: Python/Streamlit 수업용 앱
- `src/data_loader.py`: CP949·EUC-KR 등을 안전하게 처리하는 CSV 로더
- `src/analysis.py`: 변화량, 증감률, 선형 추세, Pearson 상관계수 분석
- `src/charts.py`: matplotlib·seaborn 기반 그래프
- `src/map_view.py`: folium 기반 연도별 기온 지도와 GeoJSON 경계
- `dist/`: Cloudflare Sites에 배포하는 상호작용형 정적 대시보드
- `scripts/build_static_data.py`: CSV를 검증하고 배포용 JSON을 생성
- `tests/`: 데이터 로더와 핵심 분석값 검증

Cloudflare 정적판은 서버에서 Python을 실행하지 않는 대신, 같은 CSV를 Python으로 전처리한 `analysis.json`을 사용합니다. 로컬 Streamlit판은 실행할 때마다 CSV를 다시 읽고 분석합니다.

## 핵심 기능

- 영주·문경·영천의 연평균·평균최저·평균최고기온 그래프
- 도시·지표·기간 선택, 추세선과 원자료 표 보기
- 경북 사과 재배면적·10a당 생산량·총생산량 비교
- 도시별 기온과 경북 총생산량의 산점도·회귀 추세·상관계수
- 2012~2025 연도 슬라이더를 갖춘 기온 지도
- 학생 예상, 자료해석 퀴즈, 지역사회 대응 방안 활동
- 교사용 5~7분 시연 흐름과 교육과정 연계
- 첨부 그래프를 활용한 사전 분석 갤러리

## 중요 데이터 범위

- 기온: 영주·문경·영천 관측자료
- 농업: 경상북도 전체 사과 자료
- 기간: 2012~2025년, 14개 연도

시군별 사과 생산량 자료가 아니므로 지도에는 도시별 생산량을 표시하지 않습니다. 상관관계는 인과관계를 의미하지 않으며, 강수량·태풍·병해충·농가 수·재배기술 등 추가 변수가 필요합니다.

## 데이터 출처

- 기온 CSV: 기상청 기상자료개방포털에서 수집한 연별 기온 자료
- 사과 CSV: 사용자가 수집한 경상북도 사과 재배면적·생산량 자료
- 행정구역 경계: [southkorea/southkorea-maps](https://github.com/southkorea/southkorea-maps)의 2018 시군 GeoJSON
- 지도 타일: OpenStreetMap contributors

최종 제출 전 원자료를 내려받은 정확한 기관·표명·URL·다운로드 날짜를 과제 기획서에 추가하세요.

## Windows에서 Streamlit 실행

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다.

## 정적 발표판 실행

```powershell
python scripts\build_static_data.py
python -m http.server 8000 --directory dist
```

브라우저에서 `http://localhost:8000`을 엽니다. `dist/index.html`을 파일로 직접 열면 브라우저 보안정책 때문에 JSON을 읽지 못할 수 있습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
```

테스트는 14개 연도, 기온 기준값, 2012·2015·2025년 사과 기준값, 연도 결합, 증감률, 상관계수 범위 및 결측값 오류를 확인합니다.

## Cloudflare 배포

`.openai/hosting.json`은 `dist`를 정적 배포 디렉터리로 지정합니다. 배포 전 `python scripts/build_static_data.py`를 다시 실행해 CSV 변경사항을 반영해야 합니다.

## 5~7분 발표 흐름

1. 주제와 핵심 질문 소개
2. 도시를 바꾸며 기온 변화 비교
3. 재배면적·생산량과 상관계수 설명
4. 지도 연도 슬라이더 시연
5. 학생 퀴즈와 해결책 활동
6. 상관관계의 한계와 수업 활용 정리

## 향후 개선

- 시군별 사과 재배면적·생산량 자료 추가
- 강수량·폭염일수·태풍·병해충 자료 결합
- 30년 이상 장기 자료로 분석 기간 확장
- 학생 활동 결과를 저장하는 학급용 기능 추가
