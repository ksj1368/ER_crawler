# Eternal Return API Crawler

배틀로얄 게임 "[이터널 리턴(Eternal Return)](https://playeternalreturn.com/main?hl=ko-KR)"의 공식 API를 통해 게임 데이터 크롤링 시스템입니다. 상위 랭커들의 경기 데이터를 수집하여 메타 분석과 통계 분석을 위한 데이터셋을 구축합니다.

## 주요 기능

### 데이터 수집 및 처리
이터널 리턴의 다양한 데이터를 수집하고 처리합니다. 상위 랭커 목록을 기반으로 각 플레이어의 최근 매치 정보, 플레이어 통계, 특성, 장비 정보, 크레딧 내역 등 경기 데이터를 수집합니다. 수집된 json 데이터는 구조화된 형태로 파싱되어 데이터베이스 스키마에 맞게 변환됩니다.

### 데이터베이스 스키마
게임의 주요 요소를 저장할 수 있는 정규화된 데이터베이스 스키마를 설계했습니다. 매치 정보, 팀 데이터, 플레이어 기본 정보, 장비 및 무기, 피해량, 특성 선택, MMR 변화, 크레딧 획득 내역 등 20여 개의 테이블로 구성되어 있습니다.

## 기술 스택 및 프로젝트 구조

### 개발 환경 및 언어
- `Python`, `Poetry`, `MySQL`

## 프로젝트 구조

```
📦 ER_Crawler
├─db
│  └─ schema.sql
├─docs
│  ├─ ERD
│  │  └─ erd.vuerd.json
│  └─ data_statement
│     ├─ Docs_KR_20250403.pdf
│     └─ l10n-Korean-20250417055750.txt
├─ scripts
│  ├─ __init__.py
│  ├─ crawler.py
│  ├─ db_utils.py
│  ├─ init_db.py
│  ├─ main.py
│  ├─ parsing.py
│  └─ utils.py
├─ .gitignore
├─ README.md
├─ poetry.lock
└─ pyproject.toml
```

### 모듈별 역할
`crawler.py`: 이터널 리턴 공식 API를 호출하여 상위 랭커 정보, 매치 데이터, 캐릭터 정보, 장비 데이터 등을 수집

`parsing.py`: 수집된 원시 JSON 데이터를 데이터베이스 스키마에 맞는 구조화된 형태로 변환

`db_utils.py`: 커넥션 풀링, 배치 삽입, 중복 검사 등 데이터베이스 설정 

`utils.py`: 로깅, 배치 처리, 멀티프로세싱 등 시스템에 필요한 유틸리티 설정

## 설치 및 설정
### 프로젝트 설치
```bash
# 저장소 클론
git clone 
cd ER-crawler

# Poetry를 통한 의존성 설치
poetry install

# 가상환경 활성화
poetry shell
```

### 환경 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 설정 추가
```env
# API 설정
API_KEY=your_eternal_return_api_key

# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=ER_Dataset

# 경로 설정
schema_path=./db/schema.sql
log_path=./logs/

# 변수 설정
season_id = 31 # 수집할 게임 시즌
matching_mode = 3 # 게임 모드 (1: 솔로, 2: 듀오, 3: 스쿼드)
main_version = 46 # 게임 패치 버전
```

### DB 초기화
```bash
# 데이터베이스 스키마 생성
poetry run python scripts/init_db.py
```

## 사용 방법
```bash
poetry run python scripts/main.py
```

### 실행 과정
1. 지정된 시즌의 상위 랭크 유저 목록 호출
2. 지정된 패치 버전에 해당하는 유저의 최근 경기 ID를 비동기적으로 수집
3. 수집된 매치 ID의 경기 데이터를 배치 단위로 요청
4. 멀티프로세싱을 통해 동시에 여러 경기 데이터를 파싱하고 데이터베이스에 저장

## 데이터 설명
[Notion](https://feather-bone-09d.notion.site/1e3fa3b7aa8280d3b86ee72002aa98ea?pvs=4) 참고