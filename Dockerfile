# Base image pinned by manifest digest for reproducible builds and controlled security updates
FROM python:3.12.13-alpine3.22@sha256:a190708a2dec1bd18b1decb539f8e8f5407abaa9bf39cacda583f7f8c11db322 AS builder

# Avoid .pyc files, enable unbuffered stdout logging and configure the virtual environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Update Alpine packages before installing Python dependencies
RUN apk update && apk upgrade --no-cache

WORKDIR /build

# Install runtime dependencies in an isolated virtual environment
COPY requirements.txt .

RUN python -m venv "$VIRTUAL_ENV" && \
    python -m pip install --upgrade "pip>=26,<27" --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt && \
    pip check && \
    rm -rf "$VIRTUAL_ENV/lib/python3.12/site-packages/pip" \
           "$VIRTUAL_ENV/lib/python3.12/site-packages/pip-"*.dist-info \
           "$VIRTUAL_ENV/bin/pip" \
           "$VIRTUAL_ENV/bin/pip3" \
           "$VIRTUAL_ENV/bin/pip3.12"


# Base image pinned by manifest digest for reproducible builds and controlled security updates
FROM python:3.12.13-alpine3.22@sha256:a190708a2dec1bd18b1decb539f8e8f5407abaa9bf39cacda583f7f8c11db322 AS runtime

# Avoid .pyc files, enable unbuffered stdout logging and use the copied virtual environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Update Alpine packages and remove package-management tooling not required at runtime
RUN apk update && \
    apk upgrade --no-cache && \
    rm -rf /usr/local/lib/python3.12/site-packages/pip \
           /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
           /usr/local/bin/pip \
           /usr/local/bin/pip3 \
           /usr/local/bin/pip3.12 \
           /usr/local/lib/python3.12/ensurepip

# Create a non-root user with a fixed UID for better runtime security
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

WORKDIR /app

# Copy only the installed runtime dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application source with non-root ownership
COPY --chown=appuser:appuser application ./application

# Gunicorn runtime settings for predictable performance
ENV GUNICORN_CMD_ARGS="--workers=2 --threads=2 --timeout=60 --graceful-timeout=30 --access-logfile - --error-logfile -"

EXPOSE 8000

USER appuser

# Health check against /healthz
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').getcode()==200 else 1)"

# Gunicorn target: <module>:<Flask app>
CMD ["gunicorn", "-b", "0.0.0.0:8000", "application.app:app"]