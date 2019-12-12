FROM python:3.7
ENV PYTHONUNBUFFERED 1

WORKDIR ../..
RUN mkdir /www
WORKDIR /www
COPY requirements.txt /www/
RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY . /www/
