FROM node:18-slim AS frontend-builder

WORKDIR /app
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# ---

FROM python:3.11-slim

WORKDIR /app

# Install Node.js runtime (no es necesario instalar npm nuevamente)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend ./backend

# Copy frontend built files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 5000

# Usar gunicorn para ejecutar la app
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]