FROM python:3.11-slim

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
# Install Chrome (Debian 12 compatible)
# ---------------------------------------------------------
RUN wget -q -O /usr/share/keyrings/google-linux-signing-key.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Install ChromeDriver matching Chrome version
# ---------------------------------------------------------
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) && \
    DRIVER_URL="https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${MAJOR_VERSION}" && \
    DRIVER_VERSION=$(wget -qO- $DRIVER_URL) && \
    wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver-linux64*


ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# ---------------------------------------------------------
# Copy project + install dependencies
# ---------------------------------------------------------
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip wheel setuptools
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "flask_app.py"]
