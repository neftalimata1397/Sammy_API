FROM python:3.11-slim

WORKDIR /app

# Evita que Python genere archivos .pyc y fuerza salida sin búfer para ver logs en vivo
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

CMD ["python", "run_monthly_export.py"]