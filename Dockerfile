FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY . /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000