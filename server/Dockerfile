FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app
COPY server/scripts ./scripts

ENV UPLOAD_DIR=/app/uploads
ENV DATABASE_URL=postgresql+asyncpg://checkin:checkin@db:5432/checkin

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
