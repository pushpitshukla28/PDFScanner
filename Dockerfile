# Use official Python image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your scripts
COPY app.py .
COPY main.py .

# Create empty input/output directories
RUN mkdir -p input output

# Use ENTRYPOINT for the python command, CMD for default script
ENTRYPOINT ["python"]
CMD ["app.py"]