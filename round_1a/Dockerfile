# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for pdfminer.six
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements_1a.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_1a.txt

# Copy the main application
COPY main.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set permissions
RUN chmod +x main.py

# Run the application
CMD ["python", "main.py"]