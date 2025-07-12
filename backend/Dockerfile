# Stage 1: Builder - Install all dependencies
FROM python:3.11-slim as builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# First copy only requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime - Create the final, lean image
FROM python:3.11-slim as runtime

WORKDIR /app

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY . .

# Change ownership to the non-root user
RUN chown -R app:app /app
USER app

# Expose the port the app runs on
EXPOSE 8000

# Run the application with Gunicorn, a production-grade WSGI server
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "app.main:app"]