# LinkForge — URL Shortener API

A production-ready URL shortening REST API built with Flask, Redis, and MySQL. Features Redis caching, click analytics, URL expiry, rate limiting, user authentication, and full Docker support.

## Live Demo
> Deployed locally with Docker. Clone and run in 2 commands.

## Tech Stack
- Python 3.11, Flask
- MySQL (SQLAlchemy ORM)
- Redis (cache-aside pattern)
- bcrypt password hashing
- JWT authentication (flask-jwt-extended)
- Docker + Docker Compose
- Swagger UI via Flasgger
- pytest (13 tests)

## Features
- `POST /shorten` — shorten any URL with optional expiry
- `GET /<code>` — redirect to original URL (Redis cache-aside)
- `GET /analytics/<code>` — click count, expiry, status
- `GET /urls` — list all URLs owned by logged-in user
- `DELETE /urls/<code>` — delete your own URL
- `POST /register` — create account
- `POST /login` — returns JWT access + refresh tokens
- `GET /me` — current user details
- Rate limiting — 20 requests/min on shorten, 5/min on auth

## How Caching Works
Every redirect checks Redis first. On a cache hit, the request never touches MySQL. On a miss, MySQL is queried, the result is stored in Redis with a 1-hour TTL, then the user is redirected. Repeated visits to the same URL are essentially free from a database perspective.

## Run Locally with Docker
```bash
git clone https://github.com/sai-ganesh003/linkforge
cd linkforge
# add your DATABASE_URL, JWT_SECRET_KEY, REDIS_URL to docker-compose.yml
docker-compose up --build
```

## Run Locally without Docker
```bash
git clone https://github.com/sai-ganesh003/linkforge
cd linkforge
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# create .env with DATABASE_URL, JWT_SECRET_KEY, REDIS_URL
python run.py
```

## Run Tests
```bash
pytest test_app.py -v
```
13 tests covering URL shortening, redirect, analytics, auth, and edge cases.

## Environment Variables
```
DATABASE_URL=mysql+pymysql://user:password@host:port/dbname
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0
```
## Project Structure
linkforge/
├── app/
│   ├── init.py        # App factory, Redis init
│   ├── config.py          # Environment config
│   ├── models.py          # User, URL models
│   ├── routes/
│   │   ├── auth.py        # Register, login, me
│   │   └── url.py         # Shorten, redirect, analytics
│   └── utils/
│       ├── shortener.py   # Base62 code generator
│       └── rate_limiter.py # Redis-based rate limiting
├── test_app.py            # pytest suite
├── Dockerfile
├── docker-compose.yml
└── run.py