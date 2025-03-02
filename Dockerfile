FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    procps \
    build-essential \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    gcc \
    && apt-get remove -y build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/discord-bot

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .


CMD ["python3", "run.py"]
