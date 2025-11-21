FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY admin_panel/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files from admin_panel directory
COPY admin_panel/ /app/

# Copy data and config directories for import command
COPY data/ /data/
COPY config/ /config/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script (migrates DB, collects static, starts gunicorn)
CMD ["/app/entrypoint.sh"]
