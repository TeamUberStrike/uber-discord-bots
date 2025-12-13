# Stage 1: Build
FROM python:3.14-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy Poetry files and install dependencies inside build environment
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY app /app

COPY .env /app

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Copy installed packages and app from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /app /app

CMD ["python", "vetoauto.py"]
