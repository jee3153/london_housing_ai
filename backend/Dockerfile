FROM python:3.12-slim

# Install system dependencies for psycopg2, etc.
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install Poetry and configure it to install system-wide
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

COPY . .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["bash"]
