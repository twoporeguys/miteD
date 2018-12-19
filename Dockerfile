FROM python:3.6

COPY ./ /app
WORKDIR /app

RUN python3 setup.py install
