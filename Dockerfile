# ========================================================
# WasteWiseAI - Multi-stage Production Dockerfile for Render
# ========================================================

# Stage 1: Build React 18 + Vite + Tailwind Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python 3.11 Backend & ONNX Runtime (CPU)
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install minimal OS dependencies for ONNX Runtime CPU & image decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and configurations
COPY app/ ./app/
COPY config/ ./config/
COPY models/ ./models/
COPY demo/ ./demo/

# Copy static frontend build from Stage 1 into web/dist
COPY --from=frontend-builder /web/dist ./web/dist

# Expose Render HTTP port
EXPOSE 8000

# Health check probe for Render
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Launch FastAPI with Uvicorn (binds dynamically to Render's assigned $PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

