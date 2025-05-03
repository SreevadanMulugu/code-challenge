# ---------- Base image ----------
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---------- System deps ----------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential git curl poppler-utils swig && \
    rm -rf /var/lib/apt/lists/*

# ---------- Python deps ----------
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- Workspace ----------
COPY . /app
CMD ["bash"]      # container opens an interactive shell; candidates run what they like