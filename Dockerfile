FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 "uvicorn[standard]==0.32.1" "psycopg[binary]==3.2.3"
COPY core core
COPY api api
COPY db db
COPY data data
