FROM python:3.12

WORKDIR /app
COPY src/ /app
COPY data/london.csv /data/london.csv
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
