# Use Python base image compatible with AMD64
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Copy the main script
COPY app.py .

# Set the default command
CMD ["python", "app.py"]