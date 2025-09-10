# Docker Setup for Record Label Manager

## Overview

This document describes the Docker setup for the Record Label Manager application, which consists of three main services:

1. **Backend**: Django REST API with Django Admin
2. **Frontend**: React/Vite application
3. **Database**: PostgreSQL

## Docker Components

### Docker Compose

The application uses Docker Compose to orchestrate multiple containers. The main configuration is defined in `docker-compose.yml`.

### Services

#### 1. Database (PostgreSQL)
- **Image**: postgres:15
- **Environment Variables**:
  - POSTGRES_PASSWORD=postgres_password
  - POSTGRES_USER=postgres_user
  - POSTGRES_DB=label_manager
- **Persistent Volume**: postgres_data

#### 2. Backend (Django)
- **Build**: Custom Dockerfile in ./backend
- **Environment Variables**:
  - DJANGO_SETTINGS_MODULE=label_manager.settings_docker
  - PYTHONUNBUFFERED=1
  - DEBUG=0
  - SECRET_KEY=your_production_secret_key_here
  - DATABASE_URL=postgres://postgres_user:postgres_password@db:5432/label_manager
  - ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
  - CORS_ALLOWED_ORIGINS=http://localhost,https://yourdomain.com
- **Volumes**:
  - static_volume:/app/staticfiles
  - media_volume:/app/media
- **Dependencies**: db

#### 3. Frontend (Nginx + React)
- **Build**: Dockerfile in project root
- **Ports**: 80:80 (exposes the application to host port 80)
- **Volumes**:
  - static_volume:/usr/share/nginx/html/static
- **Dependencies**: backend

### Volumes
- **postgres_data**: Persistent database storage
- **static_volume**: Shared volume for static files between backend and frontend
- **media_volume**: Storage for uploaded media files

## Configuration Files

### Backend Dockerfile
- Located at `./backend/Dockerfile`
- Installs Python dependencies from requirements.txt
- Collects static files during the build process
- Runs Gunicorn as the WSGI server

### Frontend Dockerfile
- Located at `./Dockerfile`
- Builds the React application
- Sets up Nginx to serve the frontend and proxy requests to the backend

### Nginx Configuration
- Located at `./nginx/nginx.conf`
- Serves the React frontend
- Proxies API requests to the Django backend
- Handles static and media file serving
- Manages routing for the Django admin interface

## Django Settings

The Django application uses a Docker-specific settings file `settings_docker.py` which:

1. Connects to the PostgreSQL database in the db container
2. Uses Whitenoise middleware to serve static files
3. Sets appropriate allowed hosts and CORS settings
4. Configures static files to be collected to `/app/staticfiles`

## Running the Application

### Starting the Containers
```bash
docker-compose up -d
```

### Creating a Superuser
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Collecting Static Files
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

### Accessing the Application
- **Frontend**: http://localhost/
- **Django Admin**: http://localhost/admin/
- **API**: http://localhost/api/

## Troubleshooting

### Static Files Not Loading
If static files are not loading properly in the Django admin:
1. Ensure static files are collected: `docker-compose exec backend python manage.py collectstatic --noinput`
2. Verify volumes are mounted correctly in docker-compose.yml
3. Check that Nginx is configured to serve static files from the correct location
4. Restart the containers: `docker-compose restart`

### Database Connection Issues
If the backend can't connect to the database:
1. Ensure the database container is running: `docker-compose ps`
2. Check database environment variables in docker-compose.yml
3. Inspect database logs: `docker-compose logs db`

### Container Build Failures
If container builds fail:
1. Try building with no cache: `docker-compose build --no-cache`
2. Check Dockerfile syntax and paths
3. Verify all required files exist in the expected locations
