FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=djangoProject.settings

WORKDIR /app
COPY . /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN pip list

EXPOSE 8000