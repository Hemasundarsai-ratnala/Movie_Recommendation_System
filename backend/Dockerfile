FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and data
COPY data/ ./data/
COPY backend/ ./backend/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Train models during container build
RUN python backend/scripts/train.py

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
