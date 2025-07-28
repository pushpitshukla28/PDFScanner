# Use a slim, official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# --- FIX IS HERE ---
# Copy the requirements file from the current directory
COPY requirements_1a.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_1a.txt

# --- AND FIX IS HERE ---
# Copy the main script from the current directory
COPY main.py .

# This command will be executed when the container starts
CMD ["python", "main.py"]