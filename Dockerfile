# Use a slim, official Python base image that is compatible with the libraries
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# The --no-cache-dir flag keeps the image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application script for Round 1B
# IMPORTANT: Make sure your Python file is named 'main_1b.py'
COPY app.py .

# This command will be executed when the container starts
CMD ["python", "app.py"]
