# Dockerfile (place at repo root)
FROM python:3.11-slim

# ----- Install system dependencies -----
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    unzip \
    gnupg \
    ffmpeg \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    fonts-liberation \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xvfb \
    chromium \
    chromium-driver \
 && rm -rf /var/lib/apt/lists/*

# Set chrome executable env variables (used by Selenium)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

# ----- Create app directory -----
WORKDIR /app
COPY . /app

# Avoid cache issues while installing Python packages
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1

# ----- Install Python dependencies -----
# If your requirements file has problematic or nonexistent package names (e.g. lxml_html_clean),
# pip will fail. Edit requirements if pip fails.
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Optional: expose port used by flask_app.py (5000 by default)
EXPOSE 5000

# Ensure Flask uses 0.0.0.0 host inside container
ENV FLASK_APP=flask_app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start command — keep same entrypoint you used locally
CMD ["python", "flask_app.py"]
