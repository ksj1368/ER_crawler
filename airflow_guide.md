# Airflow 및 Docker 실행 가이드

이 문서는 이터널 리턴 데이터 수집 파이프라인을 Docker 환경에서 실행하고 관리하는 방법을 설명합니다.

## 1. 사전 요구 사항
- **Docker Desktop**이 설치되어 있고 실행 중이어야 합니다.
- 프로젝트 루트 디렉토리에 API 키 및 DB 설정 포함되어 있는 **`.env`** 파일이 있어야 합니다. 

## 2. 최초 실행
프로젝트를 처음 실행하거나, `Dockerfile` 또는 의존성이 변경되었을 때 수행합니다.

### 2.1. Docker 이미지 빌드 및 초기화
```powershell
# 1. 이미지 빌드(최신 코드 및 의존성 반영)
docker-compose build

# 2. Airflow 초기화(DB 마이그레이션 및 사용자 생성)
docker-compose up airflow-init
```
> **참고**: `airflow-init` 컨테이너가 `exited with code 0`으로 종료되면 초기화가 성공한 것입니다.

## 3. 실행 및 종료

### 3.1. 실행(백그라운드)
```powershell
docker compose up -d
```
이 명령어를 실행하면 다음 컨테이너들이 실행됩니다:
- `airflow-webserver`: 웹 UI (포트 8080)
- `airflow-scheduler`: DAG 스케줄링 및 실행
- `postgres`: Airflow 메타데이터 DB
- `er_mysql`: 수집 데이터 저장소 (외부 접속 포트: **3307**)

### 3.2. 상태 확인
```powershell
docker ps
```
모든 컨테이너의 STATUS가 `Up` 상태인지 확인합니다.

### 3.3. 서비스 종료
```powershell
docker-compose down
```
모든 컨테이너와 네트워크를 정리합니다. 데이터 볼륨(DB 데이터)은 보존됩니다.

## 4. Airflow 웹 UI 접속 및 사용

1.  **접속 주소**: [http://localhost:8080](http://localhost:8080)
2.  **로그인**:
    - ID: `airflow`
    - PW: `airflow`
3.  **DAG 실행**:
    - 메인 화면에서 `eternal_return_crawler_v1`을 찾습니다.
    - 왼쪽의 **Pause/Unpause 토글**을 클릭하여 **Unpause (파란색)** 상태로 만듭니다.
    - 우측의 **Actions** 열에서 `▶` (Trigger DAG) 버튼을 누르면 즉시 실행됩니다.

## 5. 데이터베이스 접속 정보
localhost에서 DB로 접속할 때 사용합니다.

- **Host**: `localhost`
- **Port**: `3307`
- **Database**: `erdb`
- **User**: `root`
- **Password**: `password`

## 6. 문제 해결 (Troubleshooting)

### Q. "localhost에서 연결을 거부했습니다" → 포트 연결 실패
- 컨테이너가 아직 부팅 중일 수 있습니다. `docker ps`로 `health: starting` 상태인지 확인하고 잠시 기다리세요.
- 포트 충돌이 발생했을 수 있습니다. `docker-compose logs er_mysql` 등으로 에러를 확인하세요.

### Q. Docker 명령어가 먹통이거나 "input/output error" 발생
- Docker Desktop 자체의 문제입니다.
- **해결**: 트레이 아이콘 우클릭 -> **Quit Docker Desktop** 후 다시 실행하세요.

### Q. 코드 수정 후 반영이 안 될 때
- Python 코드를 수정했다면 이미지를 다시 빌드하거나 컨테이너를 재시작해야 합니다.
```powershell
docker-compose restart airflow-webserver airflow-scheduler
# 또는
docker-compose up -d --build
```
