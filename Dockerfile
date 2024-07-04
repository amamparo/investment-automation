FROM amazon/aws-lambda-python:3.11

RUN yum update -y && yum install -y wget xorg-x11-fonts-75dpi xorg-x11-fonts-misc \
    ipa-gothic-fonts xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 unzip atk java-1.8.0-openjdk \
    cups-libs libXcomposite libXcursor libXdamage libXext libXi libXrandr libXScrnSaver libXtst \
    pango alsa-lib at-spi2-atk at-spi2-core libX11 GConf2 nss libcups2 libXss1 fonts-liberation \
    libappindicator1 libnss3 lsb-release xdg-utils libxkbcommon && \
    yum clean all

COPY . ${LAMBDA_TASK_ROOT}
COPY src/ ${LAMBDA_TASK_ROOT}/src
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install
RUN poetry run playwright install chromium --with-deps

RUN poetry export > requirements.txt
RUN pip install -r requirements.txt