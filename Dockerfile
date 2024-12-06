FROM ubuntu:20.04
WORKDIR /usr/src

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update
RUN apt-get upgrade -y  # apt-upgrade -> apt-get upgrade로 수정
RUN apt-get install  wget unzip python3-pip python3 xvfb libx11-dev libxkbfile-dev   -y
COPY ./src/google-chrome-stable_current_amd64.deb .
RUN apt-get -y install ./google-chrome-stable_current_amd64.deb
COPY ./src/chromedriver-linux64.zip /tmp/chromedriver.zip
RUN unzip /tmp/chromedriver.zip -d /usr/src/chrome  # 압축 해제
RUN unzip -l /tmp/chromedriver.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .


CMD [ "xvfb-run","-a","python3", "main.py" ]