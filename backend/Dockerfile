# Backend FastAPI — pipeline PDF→Markdown. Python 3.13 slim.
FROM python:3.13-slim

# libgl1 + libglib2.0-0: opencv (via rapidocr) precisa deles em runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala deps primeiro (cache de camada); pyproject define o pacote app*.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

ENV PDF2MD_OUTPUT_DIR=/data/output
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
