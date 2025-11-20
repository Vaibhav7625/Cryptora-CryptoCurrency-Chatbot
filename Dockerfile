FROM python:3.11-slim

# Avoid TZ prompt
ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------
# Install system dependencies
# ---------------------------------------------------------
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
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libu2f-udev \
    fonts-liberation \
    xvfb \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Install Chrome (official Google Chrome stable)
# ---------------------------------------------------------
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Install ChromeDriver matching Chrome version
# ---------------------------------------------------------
RUN CHROME_VERSION=$(google-chrome --version | sed 's/[^0-9.]//g' | cut -d '.' -f 1) && \
    echo "Chrome major version: $CHROME_VERSION" && \
    wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O LATEST && \
    DRIVER_VERSION=$(cat LATEST) && \
    wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip LATEST

# Tell Selenium where Chrome and Chromedriver live
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# ---------------------------------------------------------
# Create app folder & install Python deps
# ---------------------------------------------------------
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip wheel setuptools
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "flask_app.py"]
