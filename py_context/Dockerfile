# Use a specific version of Debian as the base image
FROM debian:bookworm-slim

# Switch to root user
USER root

# Set the working directory
WORKDIR /work

# Install dependencies and SSL certificates
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    xvfb \
    python3 \
    python3-venv \
    xauth \
    dbus \
    libxss1 \
    libgbm1 \
    libappindicator1 \
    libnss3 \
    libasound2 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xdg-utils \
    --no-install-recommends

RUN mkdir -p /run/dbus
RUN dbus-daemon --system --fork
# Add Google's official GPG key
RUN curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-archive-keyring.gpg

# Add the Google Chrome repository
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-archive-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list

# Download and install a specific version of Google Chrome
RUN mkdir -p /opt/google && \
    curl -sSL https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.141/linux64/chrome-linux64.zip -o /tmp/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /tmp/ && \
    mv /tmp/chrome-linux64 /opt/google/chrome && \
    ln -s /opt/google/chrome/chrome /usr/bin/google-chrome


# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*


# Download and install ChromeDriver
RUN curl -sSL https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.141/linux64/chromedriver-linux64.zip -o /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file and install Python dependencies in the virtual environment
COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install -r /requirements.txt

# Copy the start script and make it executable
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

# Remove carriage return characters from start.sh (for Windows compatibility)
RUN sed -i 's/\r$//' /start.sh

# Set up the command to run when the container starts
CMD ["/start.sh"]
