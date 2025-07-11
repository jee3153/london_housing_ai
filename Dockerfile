FROM python:3.12

WORKDIR /app
COPY src/ /app

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/api /app/api

EXPOSE 7777

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
