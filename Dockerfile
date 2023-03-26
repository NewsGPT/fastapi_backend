FROM python:3.11.1-slim-bullseye
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 80

CMD cd src/newssearchbrief && uvicorn main:app --port 80 --host 0.0.0.0
