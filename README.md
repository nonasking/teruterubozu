# teruterubozu ☀️

내일 비가 오는지 매일 20시에 자동으로 확인하는 날씨 알림 서버.

## 기술 스택

- **Python** 3.11+
- **FastAPI** — HTTP 서버
- **APScheduler** — 일일 스케줄러 (매일 20:00 실행)
- **OpenWeather API** — 날씨 데이터 ([5-day forecast](https://openweathermap.org/forecast5), 무료 플랜)
- **Poetry** — 패키지 관리

## 프로젝트 구조

```
teruterubozu/
├── backend/
│   ├── main.py        # FastAPI 앱 진입점, 스케줄러 lifespan 등록
│   ├── scheduler.py   # APScheduler 설정 및 작업 등록
│   └── weather.py     # OpenWeather API 클라이언트
├── .env.example       # 환경 변수 템플릿
├── pyproject.toml
└── poetry.lock
```

## 시작하기

### 1. 의존성 설치

```bash
poetry install --no-root
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 값을 채웁니다.

| 변수 | 설명 |
|---|---|
| `OPENWEATHER_API_KEY` | [OpenWeather](https://openweathermap.org/api) API 키 |
| `OPENWEATHER_LAT` | 관측 지점 위도 (기본값: 서울) |
| `OPENWEATHER_LON` | 관측 지점 경도 (기본값: 서울) |

### 3. 서버 실행

```bash
poetry run uvicorn backend.main:app --reload
```

서버가 뜨면 APScheduler가 함께 시작되며, 매일 **20:00**에 내일 강수 여부를 확인하고 결과를 출력합니다.

```
[scheduler] tomorrow rain forecast: True
```

## 동작 방식

1. FastAPI 앱이 시작될 때 `lifespan` 훅으로 스케줄러를 등록합니다.
2. 매일 20:00, `get_tomorrow_weather()`가 OpenWeather 5-day forecast API를 호출합니다.
3. 내일 날짜의 예보 항목 중 강수 관련 코드(2xx 천둥번개, 3xx 이슬비, 5xx 비)가 하나라도 있으면 `True`를 반환합니다.
4. 결과를 콘솔에 출력합니다.
