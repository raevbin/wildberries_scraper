FROM python:3
RUN mkdir /data
WORKDIR /data
ADD requirements.txt /data
RUN apt-get update
RUN pip install -r requirements.txt
RUN cd / && wget http://download.redis.io/releases/redis-5.0.7.tar.gz
RUN cd / && tar xzf redis-5.0.7.tar.gz && cd redis-5.0.7 && make
RUN apt-get install -y redis-tools
RUN apt install sqlite3
