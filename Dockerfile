FROM python:3.11

WORKDIR /app
COPY . /app

RUN pip install flask pymongo pika python-dotenv

EXPOSE 5000
CMD ["python", "app.py"]
