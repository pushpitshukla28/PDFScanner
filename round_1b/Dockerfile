# Use a slim, official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file from the current directory
COPY requirements_1b.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_1b.txt

# Copy the main application script
COPY app.py .

# This command will be executed when the container starts
CMD ["python", "app.py"]