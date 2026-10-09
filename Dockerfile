FROM python:3.14-slim

WORKDIR /App

Copy requirements.txt .
Run pip install -r requiremetns.txt

COPY main.py database.py models.py .

CMD ["uvicorn", "main:app" ,"--host", "0.0.0.0", "--port", "8000"]

