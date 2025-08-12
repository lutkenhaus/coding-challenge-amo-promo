# coding-challenge-amo-promo
This is a coding challenge created by the company Amo Promo.

# Technologies used in this project
- Python
- Django
- PostgreSQL with Psycopg2
- Docker
------------

- Django REST Fremaework (DRF)
- Requests library
- python-dotenv
- pytest with pytest-django
- gunicorn
- linter (Black)

# Requirements

- Python version: 3.13.5
- Psycopg2 version:
- Docker version: 28.3.2
- Docker Compose version: v2.38.2
- 

# Installation

- Clone the Repository

git clone <repository-url>
cd coding-challenge-amo-promo

- Environment Variables

Create a .env file in the project root with the following variables:

# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,0.0.0.0

# Airports API
AIRPORTS_API_URL=https://api.example.com/airports
API_LOGIN=your-api-login
API_PASSWORD=your-api-password
API_KEY=your-api-key
API_TIMEOUT=30

# Flights API
FLIGHTS_API_URL=https://api.example.com/flights

# Database (default values match docker-compose.yml)
POSTGRES_DB=amopromo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

- Replace your-secret-key, your-api-login, your-api-password, and your-api-key with actual values. For AIRPORTS_API_URL and FLIGHTS_API_URL, use the appropriate API endpoints.


# Running the Application

- Using Docker
Build and start the containers:  

'docker-compose up --build'

This builds the web, cron, postgres, and redis services and starts the Django development server at http://localhost:8000.

Apply database migrations:

'docker-compose exec web python manage.py migrate'

Run the airport import command (optional, if not using cron):

'docker-compose exec web python manage.py import_airports'

Access the application:

Open http://localhost:8000 in your browser.

The admin interface is available (but empty) at http://localhost:8000/admin/ (create a superuser with docker-compose exec web python manage.py createsuperuser).

Stop the containers:

'docker-compose down'

# Management Commands

- Import Airports:


'docker-compose exec web python manage.py import_airports'  
'docker-compose exec web python manage.py import_airports [--force-update] [--dry-run]'  

- --force-update: Force update all airports even if they exist.
- --dry-run: Simulate the import without making changes.


# Testing

The project includes pytest and pytest-django for testing. Tests use an in-memory cache and SQLite database to improve performance.

- Run tests:

'docker-compose exec web pytest airports/tests.py  -v'  

# Project Structure

airports/: App for handling airport data import and caching.  
flights/: App for managing flight data.  
amopromo/: Django project settings and configuration.  
Dockerfile: Defines the container image for the web and cron services.  
docker-compose.yml: Configures multi-container setup with web, cron, PostgreSQL, and Redis.  
requirements.txt: Lists Python dependencies.  

# Postman (curl) request for testing:

'http://localhost:8000/api/flights/search/?origin=POA&destination=MAO&departure_date=2025-08-15&return_date=2025-08-20'  

# REDIS CLI

Enter CLI:
- 'docker-compose exec redis redis-cli'

Show all keys:
- 'KEYS *'

Clear cache:
- 'FLUSHALL'