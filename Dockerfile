FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Expose dev port
EXPOSE 8000

# Entrypoint handles migrations then starts server
ENTRYPOINT ["/bin/sh", "-c", \
    "python notifications/manage.py migrate --noinput && \
     python notifications/manage.py runserver 0.0.0.0:8000" ]
