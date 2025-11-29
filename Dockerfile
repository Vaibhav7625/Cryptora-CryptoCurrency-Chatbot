FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------
# Install system dependencies for Newspaper3k, lxml, pydub
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    ffmpeg \
    wget \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Copy project and install Python dependencies
# ---------------------------------------------------------
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip wheel setuptools
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "flask_app.py"]
