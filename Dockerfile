FROM amazon/aws-lambda-python:3.11

# https://googlechromelabs.github.io/chrome-for-testing/
ARG CHROME_VERSION=123.0.6312.10

RUN yum update -y && yum install -y wget xorg-x11-fonts-75dpi xorg-x11-fonts-misc \
    ipa-gothic-fonts xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 unzip atk java-1.8.0-openjdk \
    cups-libs libXcomposite libXcursor libXdamage libXext libXi libXrandr libXScrnSaver libXtst \
    pango alsa-lib at-spi2-atk at-spi2-core libX11 GConf2 nss libcups2 libXss1 fonts-liberation \
    libappindicator1 libnss3 lsb-release xdg-utils libxkbcommon && \
    yum clean all

RUN wget https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip
RUN unzip chrome-linux64.zip -d /opt/
RUN ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome
RUN chmod +x /usr/bin/google-chrome
RUN rm chrome-linux64.zip
ENV CHROME_PATH="/usr/bin/google-chrome"

RUN wget https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip
RUN unzip chromedriver-linux64.zip -d /opt/
RUN ln -s /opt/chromedriver-linux64/chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver
RUN rm chromedriver-linux64.zip
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

RUN wget https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-headless-shell-linux64.zip
RUN unzip chrome-headless-shell-linux64.zip -d /opt/
RUN ln -s /opt/chrome-headless-shell-linux64/chrome-headless-shell /usr/bin/chrome-headless-shell
RUN chmod +x /usr/bin/chrome-headless-shell
RUN rm chrome-headless-shell-linux64.zip

COPY . ${LAMBDA_TASK_ROOT}
COPY src/ ${LAMBDA_TASK_ROOT}/src
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install

RUN poetry run playwright install chromium

RUN poetry export > requirements.txt
RUN pip install -r requirements.txt