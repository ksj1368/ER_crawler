# ER-crawler 프로젝트 실행 가이드

## 1. 개요

본 문서는 `ER-crawler` 프로젝트의 초기 설정, 데이터베이스 구성, 그리고 주요 실행 명령어에 대한 가이드를 제공합니다.

## 2. 프로젝트 구조

-   `/scripts`: 데이터 수집, 파싱, 저장을 담당하는 핵심 로직이 위치합니다.
-   `/alembic`: 데이터베이스 스키마 버전 관리를 위한 Alembic 파일들이 위치합니다.
-   `/data`: 개발 및 테스트에 사용되는 샘플 데이터가 저장되어 있습니다.
-   `/logs`: 애플리케이션 실행 로그 및 실패한 작업 로그가 저장됩니다.
-   `/tests`: 단위 테스트 및 통합 테스트 코드가 위치합니다.
-   `/config`: API URL 등 주요 설정 파일이 위치합니다.

## 3. 초기 설정

#### 가. 필수 프로그램 설치

-   Python 3.10 이상
-   Poetry (Python 의존성 관리 도구)

#### 나. 의존성 설치

프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 필요한 라이브러리를 설치합니다.

```bash
poetry install
```

#### 다. 데이터베이스 설정

-   이 프로젝트는 **MySQL** 데이터베이스를 사용합니다. 로컬 또는 원격 환경에 데이터베이스를 준비해야 합니다.

#### 라. 환경 변수 설정 (`.env` 파일)

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 아래 내용을 참고하여 데이터베이스 접속 정보와 Eternal Return API 키를 입력합니다.

```env
# .env 파일 예시

# MySQL 데이터베이스 접속 정보
# 형식: mysql+pymysql://<사용자>:<비밀번호>@<호스트>:<포트>/<데이터베이스명>
DB_URL="YOUR_DB_URL_HERE"

# Eternal Return Open API 키
API_KEY="YOUR_API_KEY_HERE"
```

**중요:** `.env` 파일은 민감한 정보를 포함하므로 Git 버전 관리에서 제외해야 합니다. (`.gitignore`에 추가되어 있는지 확인하세요.)

## 4. 데이터베이스 마이그레이션

이 프로젝트는 `Alembic`을 사용하여 데이터베이스 스키마를 관리합니다. 초기 설정 시 또는 스키마 변경이 있을 때마다 다음 명령어를 실행하여 최신 스키마를 데이터베이스에 적용해야 합니다.

```bash
alembic upgrade head
```

## 5. 실행 명령어

모든 실행은 `scripts/main.py`를 통해 이루어집니다.

#### 가. 초기 데이터 시딩 (상위 랭커)

파이프라인을 처음 실행하기 전, 데이터 수집의 시작점이 될 최상위 랭커 유저 정보를 데이터베이스에 저장해야 합니다.

```bash
poetry run python scripts/main.py seed
```

#### 나. 메인 파이프라인 실행

데이터베이스에 저장된 유저들의 `last_match_id`를 기반으로 새로운 게임 데이터를 수집하고, 여기서 발견된 새로운 유저를 다시 DB에 추가하는 'Snowballing' 방식으로 데이터 수집을 진행합니다.

```bash
poetry run python scripts/main.py run
```

#### 다. 정적 데이터 강제 업데이트

캐릭터, 아이템, 특성 등 게임의 메타 데이터(정적 데이터)를 강제로 다시 수집하고 저장합니다. 일반적으로 프로그램 실행 시 자동으로 데이터 유무를 확인하지만, 수동 업데이트가 필요할 때 사용합니다.

```bash
poetry run python scripts/main.py populate-static
```

## 6. 테스트

#### 가. 단위 테스트 실행

샘플 데이터를 사용하여 파싱 로직의 정확성을 검증하는 빠른 테스트입니다.

```bash
poetry run python -m unittest tests/test_parsing.py
```

#### 나. 통합 테스트 실행

실제 API를 호출하여 데이터를 가져온 후 파싱 로직을 검증하는 테스트입니다. 네트워크를 사용하므로 실행 속도가 느릴 수 있습니다.

```bash
poetry run python -m unittest tests/test_integration.py
```

## 7. 로깅

-   **실행 로그:** 모든 실행 과정의 로그는 `/logs` 디렉토리 내에 `log_YYYYMMDD_HHMMSS.txt` 형식의 파일로 저장됩니다.
-   **실패 작업 로그 (DLQ):** 네트워크 오류 등으로 여러 번의 재시도 후에도 영구적으로 실패한 작업은 `/logs/dead_letter_queue.log` 파일에 JSON 형식으로 기록됩니다.
