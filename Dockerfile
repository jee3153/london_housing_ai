FROM python:3.12

WORKDIR /app

COPY . /app

ENV PYTHONPATH=/app/src

RUN pip install -e ".[all]"

EXPOSE 8000

CMD ["uvicorn", "london_housing_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]