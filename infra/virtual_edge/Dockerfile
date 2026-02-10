FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt==1.6.1 python-dotenv==1.0.0

COPY src/ .

CMD ["python", "main.py"]
