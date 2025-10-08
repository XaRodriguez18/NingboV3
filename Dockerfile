# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Ensure Python output is unbuffered for logging
ENV PYTHONUNBUFFERED=1

# Default command (adjust as needed)
CMD ["python", "-u", "bot.py"]