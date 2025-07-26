# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy both main.py and app.py
COPY main.py .
COPY app.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Default command (can be overridden)
CMD ["python", "main.py"]
