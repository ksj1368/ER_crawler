# Eternal Return Crawler
- WIP
## 주요 기능

-   **데이터 수집**: 이터널 리턴 Open API를 활용하여 매치 데이터 수집
-   **비동기 처리**: `aiohttp`와 `asyncio`를 사용하여 API 요청을 비동기적으로 처리하여 데이터 수집
-   **데이터 파싱 및 저장**: 수집된 원시 데이터를 Pandas DataFrame으로 파싱하고, SQLAlchemy를 통해 MySQL DB에 저장
-   **데이터 관리**: 게임의 정적 데이터(캐릭터, 아이템 등)를 별도로 관리하여 DB에 저장

## 기술 스택 및 프로젝트 구조

### 기술 스택

-   **언어**: `Python` 3.10+
-   **데이터 수집**: `requests`, `aiohttp`
-   **데이터 처리**: `pandas`
-   **데이터베이스**: `pymysql`, `SQLAlchemy`
-   **설정 관리**: `python-dotenv`
-   **의존성 관리**: `poetry`

### 프로젝트 구조

```
eternal_return_crawler/
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── README.md
├── db/
│   └── schema.sql
├── scripts/
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   ├── crawler.py
│   ├── hash_info_parsing.py
│   ├── match_info_parsing.py
│   ├── db_utils.py
│   ├── init_db.py
│   ├── config.py
│   └── logger.py
└── logs/
```

## 모듈별 역할

-   **`main.py`**: 전체 파이프라인을 실행하는 메인 스크립트입니다. 정적 데이터를 먼저 채운 후, 매치 데이터 수집 파이프라인을 실행
-   **`pipeline.py`**: 데이터 수집, 처리, 저장을 총괄하는 파이프라인입니다. 상위 랭커 목록을 가져오고, 새로운 매치 ID를 필터링한 후, 배치 단위로 매치 데이터를 처리하여 DB에 저장
-   **`crawler.py`**: 이터널 리턴 Open API와 통신하여 데이터를 가져오는 함수와 `aiohttp`를 사용한 비동기 함수 포함
-   **`hash_info_parsing.py`**: 게임의 정적 데이터(캐릭터, 아이템 등)를 파싱
-   **`match_info_parsing.py`**: 매치 상세 데이터를 파싱하여 테이블별 DataFrame으로 변환
-   **`db_utils.py`**: SQLAlchemy를 사용하여 데이터베이스 연결, 데이터 저장, SQL 파일 실행 등 DB 관련 함수
-   **`init_db.py`**: 스키마 파일을 읽어 데이터베이스와 테이블을 초기화 후 생성
-   **`config.py`**: API 키, 데이터베이스 정보, 경로 등 프로젝트의 주요 설정을 관리하는`.env` 파일로부터 환경 변수를 로드
-   **`logger.py`**: 로깅 설정을 담당하여 파일 및 콘솔에 로그를 출력

## 설치 및 설정

1.  **Poetry 설치**:
    ```bash
    pip install poetry
    ```

2.  **의존성 설치**:
    ```bash
    poetry install
    ```

3.  **`.env` 파일 생성**:
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 알맞게 력

    ```env
    API_KEY="YOUR_ETERNAL_RETURN_API_KEY"

    # DB connection info
    DB_HOST="localhost"
    DB_PORT=3306
    DB_NAME="YOUR_DATABASE_NAME"
    DB_USER="root"
    DB_PASSWORD="YOUR_DATABASE_PASSWORD"

    # Project settings
    code_root="./eternal_return_crawler" # 프로젝트 루트 경로
    season_id=33
    matching_mode=3
    main_version=7
    region_id=10
    ```

## DB 초기화

다음 스크립트를 실행하여 데이터베이스와 테이블 생성

```bash
poetry run python scripts/init_db.py
```

## 사용 방법

-   **정적 데이터 채우기**: `main.py`를 실행하면 `populate_static_tables()` 함수가 호출되어, DB에 정적 데이터가 없으면 자동으로 채움
-   **매치 데이터 수집**: `main.py`의 `run_pipeline()` 함수가 매치 데이터 수집

## 실행 방법

프로젝트의 모든 기능을 실행하려면 `main.py`를 실행

```bash
poetry run python scripts/main.py
```
