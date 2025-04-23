FROM python:3.10

# Poetry install
RUN pip install poetry

WORKDIR /app

# Poetry 관련 파일 복사 및 의존성 설치
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --only main

# Source copy
COPY . .