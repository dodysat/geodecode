# Use a slim python image
FROM python:3.11-slim-bookworm

# Install system dependencies for GDAL and GeoPandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    g++ \
    curl \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory
RUN mkdir -p data

# Pre-download data during build (optional, but makes image heavy)
# RUN python download_data.py

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
