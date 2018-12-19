FROM python:3.7.0

WORKDIR /twitbot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/twitbot/auto.py"]