FROM python:3.11-slim

WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Build frontend
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# Move to app root and expose port
WORKDIR /app
EXPOSE 5000

# Start the backend
CMD ["python", "backend/main.py"]