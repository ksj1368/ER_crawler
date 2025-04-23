1. API 요청
2. ERD
3. work flow
4. 라이브러리 설치
5. db 연동
6. 

## Poetry
### install 
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
poetry --version 
```
- if `poetry --version` is not working in Windows OS
    - Windows 키 + 검색 → 시스템 환경 변수 편집 클릭
    - [환경 변수] 버튼 클릭
    - 사용자 변수 or 시스템 변수 중 Path 선택 → [편집]
    - [새로 만들기] 클릭
    - 다음 경로 입력:
    
        ```powershell
        C:/Users/AppData/Roaming/Python/Scripts
        ```

```bash
cd project folder
poetry init
poetry install
poetry env activate
poetry run python scripts/main.py
```
### update
```bash
# 패키지 업데이트
poerty update
# 하나씩 지정해서 업데이트도 가능
poetry update requests toml
# 업데이트는 하지 않고 poetry.lock 만 업데이트
poerty update --lock
```