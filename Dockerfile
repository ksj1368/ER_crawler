FROM apache/airflow:2.7.3-python3.10

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Update PATH to include local bin
ENV PATH="${PATH}:/home/airflow/.local/bin"

# Install poetry as airflow user
RUN pip install --user poetry==1.8.4

# Copy project files
WORKDIR /opt/airflow
COPY --chown=airflow:root pyproject.toml poetry.lock ./

# Install dependencies
# We use poetry to export requirements and then pip to install them globally in the container
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install --user --no-cache-dir -r requirements.txt

# Copy project source code
COPY --chown=airflow:root scripts/ /opt/airflow/scripts/
COPY --chown=airflow:root config/ /opt/airflow/config/
COPY --chown=airflow:root alembic/ /opt/airflow/alembic/
COPY --chown=airflow:root db/ /opt/airflow/db/
COPY --chown=airflow:root alembic.ini /opt/airflow/alembic.ini

# Set environment variables
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
ENV CODE_ROOT="/opt/airflow"