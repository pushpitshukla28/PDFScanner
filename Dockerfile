# Use a slim, official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- CHANGE THIS LINE ---
COPY app.py .

# --- AND CHANGE THIS LINE ---
CMD ["python", "app.py"]