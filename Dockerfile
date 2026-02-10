FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ✅ requirements.txt is INSIDE backend/
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ✅ copy whole repo
COPY . /app

# ✅ make start script executable
RUN chmod +x /app/start.sh

# ✅ Django lives in backend/
WORKDIR /app/backend

EXPOSE 8000

CMD ["bash", "/app/start.sh"]
