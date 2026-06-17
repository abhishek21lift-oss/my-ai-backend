FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg + psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/start.sh

# Web service: run migrations then start server.
# Worker service overrides this via dockerCommand in render.yaml.
CMD ["sh", "scripts/start.sh"]
