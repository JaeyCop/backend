# Recipe Scraper API v2.0

A comprehensive, production-ready FastAPI application for scraping recipes with advanced user authentication, caching, performance monitoring, and extensive features.

## 🚀 Features

### Core Functionality
- **Recipe Scraping**: Automated scraping from multiple recipe websites
- **Video Integration**: YouTube video tutorials for recipes
- **Advanced Search**: Multi-filter search with caching
- **Meal Planning**: Automated meal plan generation
- **Nutrition Analysis**: Recipe nutrition information
- **Recipe Recommendations**: AI-powered recipe suggestions

### User Management & Authentication
- **JWT Authentication**: Secure token-based authentication
- **User Registration/Login**: Complete user account management
- **Password Security**: Bcrypt hashing with strength validation
- **Password Reset**: Email-based password reset flow
- **User Profiles**: Extended user profiles with preferences
- **Account Security**: Login attempt tracking and account locking
- **Role-based Access**: Admin and user roles

### Performance & Scalability
- **Redis Caching**: Advanced caching with fallback to memory
- **Database Connection Pooling**: Optimized PostgreSQL connections
- **Rate Limiting**: Configurable API rate limiting
- **Background Tasks**: Celery for async task processing
- **Response Compression**: GZip compression for API responses
- **Performance Monitoring**: Request timing and metrics

### Security Features
- **Security Headers**: Comprehensive security headers
- **CORS Configuration**: Configurable cross-origin requests
- **Input Validation**: Pydantic-based request validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **XSS Protection**: Built-in FastAPI security features

### Monitoring & Observability
- **Health Checks**: Database and cache health monitoring
- **Metrics Collection**: Prometheus metrics integration
- **Logging**: Structured logging with multiple levels
- **Error Tracking**: Comprehensive error handling
- **Performance Metrics**: Request timing and database stats

## 🛠 Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with AsyncPG
- **Cache**: Redis with fallback to memory
- **Authentication**: JWT with python-jose
- **Password Hashing**: Bcrypt via passlib
- **Task Queue**: Celery with Redis broker
- **Monitoring**: Prometheus + Grafana
- **Search**: ElasticSearch (optional)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd recipe-scraper-api
```

### 2. Environment Configuration

Copy and configure the environment file:

```bash
cp .env.example .env
```

Update the following key variables in `.env`:

```env
# Security (REQUIRED - Change in production)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/recipe_db

# Redis
REDIS_URL=redis://localhost:6379

# External APIs
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Installation Options

#### Option A: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f recipe-api

# Stop services
docker-compose down
```

#### Option B: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Installation

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login
```http
POST /api/v1/users/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get User Profile
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

### Recipe Endpoints

#### Search Recipes
```http
GET /api/v1/recipes/search?q=chicken&limit=10&include_videos=true
Authorization: Bearer <access_token>
```

#### Get Recipe Details
```http
GET /api/v1/recipes/recipe?url=https://example.com/recipe
Authorization: Bearer <access_token>
```

#### Get Recommendations
```http
GET /api/v1/recipes/recommendations?based_on=pasta&max_results=5
Authorization: Bearer <access_token>
```

### User Management Endpoints

#### Update Profile
```http
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Jane",
  "dietary_preferences": ["vegetarian", "gluten-free"],
  "favorite_cuisines": ["italian", "mexican"]
}
```

#### Change Password
```http
POST /api/v1/users/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPass123",
  "new_password": "NewPass123",
  "confirm_new_password": "NewPass123"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (REQUIRED) | - |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `DEBUG` | Enable debug mode | `false` |
| `CACHE_TTL` | Cache TTL in seconds | `3600` |

### Database Configuration

The application uses Alembic for database migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Caching Strategy

- **Recipe Search**: 1 hour TTL
- **Recipe Details**: 6 hours TTL
- **User Profiles**: 30 minutes TTL
- **Video Results**: 2 hours TTL

## 🔒 Security Features

### Authentication Security
- JWT tokens with configurable expiry
- Refresh token rotation
- Password strength validation
- Account lockout after failed attempts
- Secure password hashing with bcrypt

### API Security
- Rate limiting per IP address
- CORS configuration
- Security headers (HSTS, CSP, etc.)
- Input validation and sanitization
- SQL injection protection

### Data Protection
- Sensitive data encryption
- Secure session management
- Password reset token expiry
- Email verification workflow

## 📊 Monitoring & Metrics

### Health Checks
- Database connectivity
- Cache availability
- External API status
- Application health

### Metrics Collection
- Request/response times
- Error rates
- Cache hit/miss ratios
- Database connection pool stats
- User activity metrics

### Logging
- Structured JSON logging
- Multiple log levels
- Request tracing
- Error tracking
- Performance monitoring

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
   ```bash
   # Set production environment variables
   export DEBUG=false
   export SECRET_KEY="your-production-secret-key"
   ```

2. **Database Setup**:
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Create superuser (optional)
   python scripts/create_superuser.py
   ```

3. **Docker Deployment**:
   ```bash
   # Production docker-compose
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Scaling Considerations

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database**: Read replicas for improved performance
- **Cache**: Redis cluster for high availability
- **Background Tasks**: Multiple Celery workers
- **CDN**: Static asset delivery optimization

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run integration tests
pytest tests/integration/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running
- **Issues**: Create an issue on GitHub
- **Health Check**: Monitor `/health` endpoint
- **Metrics**: View `/metrics` endpoint for diagnostics

## 🔄 Changelog

### v2.0.0
- Enhanced user authentication system
- Advanced caching with Redis
- Performance monitoring and metrics
- Comprehensive security features
- Docker containerization
- Background task processing
- Rate limiting and security headers
- Extended user profiles and preferences
- Password reset functionality
- Admin user management
- Database connection pooling
- Structured logging and error handling