# Use slim version to keep the image lightweight
FROM python:3.10-slim

# Prevent Python from buffering logs and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (git is needed for some HF models)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install heavy AI libraries with a high timeout for stability
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy project source code
COPY . .

# 8000: FastAPI | 8501: Streamlit
EXPOSE 8000
EXPOSE 8501