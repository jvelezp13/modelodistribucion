# Deployment Guide - Sistema DxV Multimarcas v2.0

## Architecture Overview

The system has been modernized with a **FastAPI + Next.js** frontend while preserving 100% of the existing backend logic.

### Components

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PostgreSQL    │────▶│  Django Admin    │     │   Next.js UI    │
│   Database      │     │   Panel (8000)   │     │   (Port 3000)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
         │                                                 │
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐                             ┌─────────────────┐
│  Core Simulator │◀────────────────────────────│  FastAPI Backend│
│   (Python)      │                             │   (Port 8001)   │
└─────────────────┘                             └─────────────────┘
```

### Ports

- **3000**: Next.js Frontend (NEW - Modern UI)
- **8000**: Django Admin Panel (Existing - Data Management)
- **8001**: FastAPI Backend (NEW - REST API)
- **8501**: Streamlit Dashboard (Legacy - Optional)
- **5432**: PostgreSQL Database

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose installed
- Git repository cloned

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
# Database
POSTGRES_DB=nexo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# API
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 3. Build and Run

```bash
# Build all services
docker-compose build

# Start services (without legacy Streamlit)
docker-compose up -d

# Start services including legacy Streamlit
docker-compose --profile legacy up -d

# View logs
docker-compose logs -f frontend
docker-compose logs -f api
```

### 4. Access the Application

- **Modern Dashboard**: http://localhost:3000
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8001/docs
- **Legacy Streamlit** (if enabled): http://localhost:8501

### 5. Initial Setup

```bash
# Run migrations
docker-compose exec django_admin python manage.py migrate

# Create superuser
docker-compose exec django_admin python manage.py createsuperuser

# Load initial data (if applicable)
docker-compose exec django_admin python manage.py loaddata initial_data.json
```

## Development

### Local Development (without Docker)

#### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r api/requirements.txt

# Run FastAPI server
cd /path/to/project
uvicorn api.main:app --reload --port 8001
```

#### Frontend (Next.js)

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Access at http://localhost:3000
```

#### Django Admin

```bash
cd admin_panel
python manage.py runserver 8000
```

## Production Deployment

### Option 1: Easypanel (Recommended)

#### 1. Create Services

Create three separate services in Easypanel:

**Service 1: PostgreSQL Database**
- Type: Database
- Engine: PostgreSQL 15
- Database Name: `nexo`

**Service 2: Django Admin**
- Type: App
- Source: GitHub repository
- Build Path: `admin_panel`
- Port: 8000
- Environment Variables:
  - `POSTGRES_HOST`: (from database service)
  - `POSTGRES_DB`: `nexo`
  - `POSTGRES_USER`: (from database service)
  - `POSTGRES_PASSWORD`: (from database service)
  - `DJANGO_SECRET_KEY`: (generate secure key)
  - `DJANGO_ALLOWED_HOSTS`: your-domain.com

**Service 3: FastAPI Backend**
- Type: App
- Source: GitHub repository
- Dockerfile: `Dockerfile.api`
- Port: 8000 (internal)
- Environment Variables: Same as Django Admin
- Domain: api.your-domain.com

**Service 4: Next.js Frontend**
- Type: App
- Source: GitHub repository
- Build Path: `frontend`
- Port: 3000
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: https://api.your-domain.com
- Domain: your-domain.com

#### 2. Configure Domains

- Main App: `your-domain.com` → Frontend (port 3000)
- Admin Panel: `admin.your-domain.com` → Django (port 8000)
- API: `api.your-domain.com` → FastAPI (port 8000)

### Option 2: Docker Compose on VPS

```bash
# Clone repository
git clone <your-repo>
cd modelodistribucion

# Set up environment
cp .env.example .env
nano .env  # Edit with production values

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 3: Separate Hosting

- **Frontend**: Deploy to Vercel/Netlify
- **Backend**: Deploy to Railway/Render
- **Database**: Use managed PostgreSQL (AWS RDS, DigitalOcean, etc.)
- **Django**: Deploy to traditional VPS

## API Endpoints

### Available Endpoints

```
GET  /                          - Health check
GET  /api/marcas               - List available marcas
POST /api/simulate             - Execute simulation
GET  /api/marcas/{id}/comercial - Get commercial data (debug)
GET  /api/marcas/{id}/ventas   - Get sales projections
```

### Example Request

```bash
# List marcas
curl http://localhost:8001/api/marcas

# Execute simulation
curl -X POST http://localhost:8001/api/simulate \
  -H "Content-Type: application/json" \
  -d '["nutresa", "marca_ejemplo"]'
```

## Architecture Highlights

### What's Reused (100% of Backend)

✅ PostgreSQL database and all models
✅ Django Admin for data management
✅ Core Simulator (`core/simulator.py`)
✅ All Calculator classes
✅ Data Loaders (YAML and PostgreSQL)
✅ All business logic

### What's New

🆕 FastAPI REST API (minimal wrapper, ~200 lines)
🆕 Next.js + React frontend
🆕 Modern UI with Tailwind CSS
🆕 Dark blue and white color scheme
🆕 Responsive design
🆕 Better UX and performance

## Troubleshooting

### Frontend can't connect to API

```bash
# Check API is running
docker-compose ps api

# Check API logs
docker-compose logs api

# Verify NEXT_PUBLIC_API_URL environment variable
docker-compose exec frontend env | grep NEXT_PUBLIC
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify environment variables
docker-compose exec django_admin env | grep POSTGRES
```

### Build errors

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Migration from Streamlit

The legacy Streamlit dashboard is still available but optional. To use only the modern stack:

```bash
# Default: Runs Django + FastAPI + Next.js (no Streamlit)
docker-compose up -d

# With Streamlit (legacy)
docker-compose --profile legacy up -d
```

## Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f frontend
docker-compose logs -f api
docker-compose logs -f django_admin

# Check resource usage
docker stats
```

## Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres nexo > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres nexo < backup.sql
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Ensure all services are running: `docker-compose ps`
4. Review API documentation: http://localhost:8001/docs
