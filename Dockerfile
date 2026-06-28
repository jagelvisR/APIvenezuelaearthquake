# --- Stage 1: Build & Dependencies ---
FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Instalar dependencias en el directorio local de usuario
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final Slim Image ---
FROM python:3.12-alpine AS runner

WORKDIR /app

# Copiar paquetes instalados desde la stage anterior
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python", "app.py"]
