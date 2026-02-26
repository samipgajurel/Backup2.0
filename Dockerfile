FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Better cache: copy requirements first
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy rest of project
COPY . /app

RUN chmod +x /app/start.sh

WORKDIR /app/backend
EXPOSE 8000

CMD ["bash", "/app/start.sh"]