FROM node:18-slim AS frontend-builder

WORKDIR /app
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# ---

FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend ./backend

# Copy frontend built files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8080

# Usar shell script para que se expanda $PORT correctamente
SHELL ["/bin/sh", "-c"]
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}