# Use a slim, official Python base image that is compatible with the libraries
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# The --no-cache-dir flag keeps the image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy your polished application script
# This now points to app.py as requested
COPY app.py .

# This command will be executed when the container starts
# This now runs app.py
CMD ["python", "app.py"]
