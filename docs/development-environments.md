# Record Label Manager Development Environments

This document describes the two development environments available for the Record Label Manager application.

## 1. Standard Development Environment

This is the original development setup with separate services running on your local machine.

### Components

- **Backend**: Django REST API
  - Running on: http://127.0.0.1:8001
  - Started with: `python manage.py runserver 8001` (from backend directory with virtual environment activated)
  - Settings file: `label_manager/settings.py`

- **Frontend**: React/Vite application
  - Running on: http://localhost:5173
  - Started with: `npm run dev` (from project root)
  - Configured to make API calls to backend at port 8001

- **Database**: PostgreSQL
  - Running locally
  - Configured in Django settings

### Environment Setup

1. **Backend Setup**:
   ```bash
   cd backend
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 8001
   ```

2. **Frontend Setup**:
   ```bash
   # From project root
   npm install
   npm run dev
   ```

### Key Configuration

- JWT-based authentication with SimpleJWT
- Frontend configured to connect to backend at port 8001
- API base URL in frontend set to http://127.0.0.1:8001
- DRF settings allow unauthenticated read access for testing

## 2. Docker Development Environment

This is the containerized setup where all services run in Docker containers.

### Components

- **Backend**: Django REST API with Gunicorn
  - Running in Docker container
  - Settings file: `label_manager/settings_docker.py`
  - Using Whitenoise for static file serving

- **Frontend**: React/Vite with Nginx
  - Running in Docker container
  - Nginx serves static files and proxies requests to backend

- **Database**: PostgreSQL
  - Running in Docker container
  - Data persisted in Docker volume

### Environment Setup

1. **Start All Services**:
   ```bash
   docker-compose up -d
   ```

2. **Create Superuser** (first time only):
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

3. **Collect Static Files**:
   ```bash
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

### Accessing the Application

- **Frontend**: http://localhost/
- **Django Admin**: http://localhost/admin/
- **API**: http://localhost/api/

### Key Configuration

- Nginx routes requests between frontend and backend
- Static files are shared between containers via Docker volume
- Database connection configured via environment variables
- Docker-specific Django settings handle production-like environment

## Switching Between Environments

### From Standard to Docker

1. Stop local services (Ctrl+C in terminal running Django and Node)
2. Start Docker services: `docker-compose up -d`

### From Docker to Standard

1. Stop Docker services: `docker-compose down`
2. Start local backend: `cd backend && python manage.py runserver 8001`
3. Start local frontend: `npm run dev`

## Considerations

- **Development Speed**: Standard environment may provide faster feedback during development
- **Production Similarity**: Docker environment more closely matches production setup
- **Database**: Each environment uses separate database instances
- **Environment Variables**: Different between the two setups
- **Static Files**: Handled differently in each environment

For comprehensive details on the Docker setup, see [docker-setup.md](./docker-setup.md).
