FROM python:3.12-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Deshabilita el buffering de salida para logs en tiempo real
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Por razones de seguridad, creamos y usamos un usuario que no sea root
RUN adduser -u 5678 --disabled-password --gecos "" factus && chown -R factus /app
USER factus

EXPOSE 8000

# Health Check para que Docker sepa si la API se bloqueó
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Gunicorn con Uvicorn Workers para producción
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
