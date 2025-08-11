FROM python:3.13.5-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    cron \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /app/logs

# Create cron log file
RUN touch /var/log/cron.log

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "amopromo.wsgi:application"]