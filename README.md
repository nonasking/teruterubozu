# teruterubozu
![istockphoto-1248324240-612x612](https://github.com/user-attachments/assets/d09675ba-6b3a-4892-be26-4aad156bb2c9)


내일 비가 오는지 매일 20시에 자동으로 확인하고 이메일로 알림을 보내는 날씨 알림 서비스.

## 기술 스택

- **Python** 3.11+
- **FastAPI** — HTTP 서버
- **APScheduler** — 일일 스케줄러 (매일 20:00 실행)
- **OpenWeather API** — 날씨 데이터 ([5-day forecast](https://openweathermap.org/forecast5), 무료 플랜)
- **Gmail SMTP** — 이메일 알림 (표준 라이브러리, 무료)
- **GitHub Actions** — 무료 배포 (매일 20:00 KST 자동 실행)
- **Poetry** — 패키지 관리

## 프로젝트 구조

```
teruterubozu/
├── backend/
│   ├── main.py        # FastAPI 앱 진입점, 스케줄러 lifespan 등록
│   ├── scheduler.py   # APScheduler 설정 및 작업 등록
│   ├── weather.py     # OpenWeather API 클라이언트
│   └── notifier.py    # Gmail SMTP 이메일 알림
├── .github/
│   └── workflows/
│       └── weather-check.yml  # GitHub Actions 배포 워크플로우
├── run.py             # GitHub Actions 실행 진입점
├── .env.example       # 환경 변수 템플릿
├── pyproject.toml
└── poetry.lock
```

## 배포 (GitHub Actions)

서버 없이 GitHub Actions의 cron 스케줄러로 매일 오후 8시에 자동 실행됩니다. **완전 무료.**

### 1. GitHub Secrets 등록

GitHub 레포지토리 → **Settings → Secrets and variables → Actions** 에서 아래 항목 추가:

| Secret | 설명 |
|---|---|
| `OPENWEATHER_API_KEY` | [OpenWeather](https://openweathermap.org/api) API 키 |
| `OPENWEATHER_LAT` | 관측 지점 위도 (기본값: `37.5665`, 서울) |
| `OPENWEATHER_LON` | 관측 지점 경도 (기본값: `126.9780`, 서울) |
| `GMAIL_USER` | 발신 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 ([발급 방법](#gmail-앱-비밀번호-발급)) |
| `NOTIFY_TO_EMAIL` | 알림 수신 이메일 주소 |

### 2. 수동 실행 (테스트)

GitHub 레포지토리 → **Actions → Daily Weather Check → Run workflow**

### Gmail 앱 비밀번호 발급

1. Google 계정 → **보안** → **2단계 인증** 활성화
2. **앱 비밀번호** → 앱 이름 입력 → 16자리 비밀번호 복사

## 로컬 실행

### 1. 의존성 설치

```bash
poetry install --no-root
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 값을 채웁니다.

### 3. 실행

```bash
# 날씨 확인 + 비 예보 시 이메일 발송
poetry run python run.py

# FastAPI 서버 실행 (스케줄러 포함)
poetry run uvicorn backend.main:app --reload
```

## 동작 방식

1. 매일 20:00, `get_tomorrow_weather()`가 OpenWeather 5-day forecast API를 호출합니다.
2. 내일 날짜의 예보 항목 중 강수 관련 코드(2xx 천둥번개, 3xx 이슬비, 5xx 비)가 하나라도 있으면 `True`를 반환합니다.
3. 비 예보가 있으면 `send_rain_alert()`가 Gmail SMTP로 이메일을 발송합니다.
