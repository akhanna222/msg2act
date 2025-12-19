# msg2act - Knowledge Graph Platform

A powerful knowledge graph platform that ingests data from multiple sources (email, messaging, documents), extracts entities and relationships, and enables intelligent automation.

## 🚀 Current Status: Phase 1 (MVP)

✅ **Completed Features:**
- Gmail OAuth integration
- Email ingestion (historical + real-time)
- Entity extraction (people, companies, amounts, dates)
- Background task processing with Celery
- RESTful API with FastAPI
- Data encryption (OAuth tokens, sensitive data)
- Docker development environment

## 🏗️ Architecture

```
Backend: Python FastAPI + Celery
Database: PostgreSQL + Redis
NLP: spaCy + Custom extractors
Frontend: React + TypeScript (coming soon)
Deployment: Docker Compose
```

## 📋 Prerequisites

- Docker & Docker Compose
- Google Cloud Project (for Gmail OAuth)
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

## 🛠️ Quick Start

### 1. Clone and Setup Environment

```bash
cd msg2act
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and set the following required variables:

```bash
# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Optional: OpenAI for advanced features
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
6. Copy Client ID and Client Secret to `.env`

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check service health
curl http://localhost:8000/api/v1/health
```

### 5. Access Services

- **API Documentation:** http://localhost:8000/docs
- **Backend API:** http://localhost:8000
- **Flower (Celery Monitor):** http://localhost:5555
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## 📚 API Usage

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Connect Gmail Account

1. Open in browser: http://localhost:8000/api/v1/auth/google/connect
2. Authorize access to Gmail
3. You'll receive an access token

### Get Messages

```bash
curl -X GET "http://localhost:8000/api/v1/messages?limit=10"
```

### Get Entities

```bash
# Get all entities
curl -X GET "http://localhost:8000/api/v1/entities"

# Filter by type
curl -X GET "http://localhost:8000/api/v1/entities?entity_type=PERSON"

# Search
curl -X GET "http://localhost:8000/api/v1/entities?search=john"
```

### Get Entity Details

```bash
curl -X GET "http://localhost:8000/api/v1/entities/{entity_id}"
```

## 🔧 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run locally (without Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations (Alembic)

```bash
# Initialize Alembic (already done)
docker-compose exec backend alembic init alembic

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head
```

### Run Celery Worker Locally

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

### Run Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

## 📁 Project Structure

```
msg2act/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   └── utils/           # Helper functions
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Coming soon
├── docker-compose.yml
├── .env.example
├── IMPLEMENTATION_PLAN.md    # Full roadmap
└── README.md
```

## 🔐 Security Features

- **OAuth Token Encryption:** All OAuth tokens encrypted with AES-256
- **JWT Authentication:** Secure API access tokens
- **Environment Isolation:** Secrets stored in environment variables
- **CORS Protection:** Configurable allowed origins
- **SQL Injection Prevention:** SQLAlchemy ORM
- **Rate Limiting:** API rate limits (planned)

## 🗃️ Database Schema

### Key Tables

- **users** - User accounts
- **oauth_tokens** - Encrypted OAuth credentials
- **data_sources** - Connected services (Gmail, etc.)
- **messages** - Emails and messages
- **entities** - Extracted entities (people, companies, amounts)
- **entity_mentions** - Entity occurrences in messages
- **relationships** - Entity relationships (Phase 2)

## 🎯 Current Capabilities

### Email Ingestion
- ✅ Gmail OAuth connection
- ✅ Historical email import (configurable days)
- ✅ Real-time email sync
- ✅ Thread grouping
- ✅ Attachment detection
- ✅ Background sync tasks

### Entity Extraction
- ✅ People (from signatures, text, emails)
- ✅ Companies (from domains, text)
- ✅ Financial amounts (multi-currency)
- ✅ Dates
- ✅ Automatic deduplication
- ✅ Confidence scoring

### API Features
- ✅ RESTful API
- ✅ OpenAPI documentation
- ✅ Message search and filtering
- ✅ Entity search and filtering
- ✅ Entity merging
- ✅ Health monitoring

## 🚧 Coming Soon (Phase 2+)

- [ ] Graph visualization UI
- [ ] Relationship mapping
- [ ] Outlook integration
- [ ] Document upload & OCR
- [ ] Voice note transcription
- [ ] Automated action flows
- [ ] Form filling AI
- [ ] Advanced search (semantic)
- [ ] Mobile app

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for full roadmap.

## 🐛 Troubleshooting

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check container logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Access container shell
docker-compose exec backend bash
```

### Database Issues

```bash
# Reset database
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d postgres
```

### OAuth Issues

- Verify redirect URI matches exactly in Google Console
- Check that Gmail API is enabled
- Ensure credentials are in `.env`
- Clear browser cookies and try again

### Entity Extraction Not Working

```bash
# Download spaCy model
docker-compose exec backend python -m spacy download en_core_web_sm

# Restart backend
docker-compose restart backend celery-worker
```

## 📊 Monitoring

### Celery Tasks (Flower)

Access http://localhost:5555 to monitor:
- Active tasks
- Task history
- Worker status
- Task success/failure rates

### Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U msg2act -d msg2act

# Useful queries
SELECT COUNT(*) FROM messages;
SELECT COUNT(*) FROM entities;
SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;
```

## 🤝 Contributing

This project is in active development. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## 📄 License

[Add your license here]

## 📞 Support

For issues and questions:
- Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed architecture
- Review API docs at http://localhost:8000/docs
- File an issue on GitHub

---

**Built with ❤️ using FastAPI, spaCy, and PostgreSQL**
