FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=label_manager.settings_docker
ENV PYTHONUNBUFFERED=1

# Create staticfiles directory and collect static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput

# Run gunicorn with Docker-specific settings
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "label_manager.wsgi:application"]
