# Use a slim, official Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
# We will create this file on the fly during the build
COPY requirements.txt .

# Install the required packages
# Using --no-cache-dir makes the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script into the container at /app
COPY main.py .

# Create directories for input and output data
# These will be mounted as volumes when the container is run
RUN mkdir -p /app/input /app/output

# Set the command to run when the container starts
CMD ["python", "main.py"]