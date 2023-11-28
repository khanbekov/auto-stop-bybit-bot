FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements/ requirements/
COPY .env .env

RUN  pip install -r requirements/production.txt \

COPY . .

CMD ["python", "./bot.py"]
