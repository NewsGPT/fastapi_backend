FROM python:3.11.1-slim-bullseye
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
ENV Port 8000

CMD cd src/newssearchbrief && uvicorn main:app --port 8000 --host 0.0.0.0