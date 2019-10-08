FROM ubuntu:16.04
 
RUN  apt-get update
RUN  apt-get upgrade -y
RUN  apt-get update && apt-get install -y  build-essential
RUN  apt-get install -y  g++
# Install python3
RUN  apt-get install -y python3
RUN  apt-get install -y python3-dev 
RUN  apt-get install -y libgtk2.0-dev
RUN  apt-get install -y cmake
RUN  apt-get install -y python-mysqldb

# Install pip
RUN apt-get install -y wget vim
RUN wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
RUN python3 /tmp/get-pip.py
RUN pip install --upgrade pip

RUN adduser people_counter

WORKDIR /project/back_end_project

COPY requirements.txt requirements.txt

RUN pip  install -U tensorflow==1.4.0
RUN pip  install cmake
RUN pip  install distro
RUN pip  install dlib
RUN pip  install -r requirements.txt
RUN pip  install gunicorn
RUN pip install requests

COPY application application
COPY video_detection video_detection
COPY people_counter.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP people_counter.py

RUN chown -R people_counter:people_counter ./
USER people_counter

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

EXPOSE 5000
EXPOSE 8009
EXPOSE 8000
ENTRYPOINT ["./boot.sh"]
