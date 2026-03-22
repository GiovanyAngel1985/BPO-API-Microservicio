# Stage 1: Builder (instala dependencias)
FROM python:3.13-slim AS builder

WORKDIR /app

# Copia requirements primero (cache layer)
COPY requirements.txt .

# Instala dependencias en /venv
RUN python -m venv /venv --copies && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (mínimo)
FROM python:3.13-slim

# Instala solo dependencias sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copia venv del builder
COPY --from=builder /venv /venv

# Crea usuario no-root (seguridad)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /venv
USER appuser

WORKDIR /app

# Copia código
COPY --chown=appuser:appgroup . .

# Puerto y variables prod
EXPOSE 8000
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Uvicorn produción-ready
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]