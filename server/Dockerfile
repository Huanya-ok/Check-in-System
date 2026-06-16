FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app
COPY mobile ./mobile

ENV UPLOAD_DIR=/app/uploads
ENV FAISS_INDEX_PATH=/app/data/face_index.faiss
ENV DATABASE_URL=postgresql+asyncpg://checkin:checkin@db:5432/checkin

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
