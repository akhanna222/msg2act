# msg2act Quick Start (5 Minutes)

## Prerequisites
- Docker & Docker Compose installed
- Google Cloud account (free tier OK)

---

## Setup Steps

### 1. Google OAuth (2 min)
```bash
# Visit: https://console.cloud.google.com/
# → APIs & Services → Credentials → Create OAuth 2.0 Client ID
# → Application type: Web application
# → Authorized redirect URIs: http://localhost:8000/api/v1/auth/google/callback
# → Copy Client ID + Secret
```

### 2. Environment Config (1 min)
```bash
cd msg2act
cp .env.example .env
nano .env  # or vim/code .env
```

**Required fields:**
```env
SECRET_KEY=<run: openssl rand -hex 32>
ENCRYPTION_KEY=<run: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### 3. Start Services (2 min)
```bash
docker-compose up -d
```

**Wait for services** (~30 sec):
```bash
docker-compose logs -f backend | grep "Application startup complete"
# Ctrl+C when you see it
```

### 4. Open App
```
http://localhost:5173
```

Click **"Connect Gmail"** → Approve → Done!

---

## Verify It's Working

**Check Services:**
```bash
# All should be healthy
curl http://localhost:8000/api/v1/health

# Should return 200
curl http://localhost:5173
```

**Monitor Sync:**
```bash
# Watch Celery tasks
open http://localhost:5555

# Watch backend logs
docker-compose logs -f celery-worker
```

**View Data:**
```bash
# Connect to database
docker-compose exec postgres psql -U msg2act -d msg2act

# Check messages
SELECT COUNT(*) FROM messages;
SELECT COUNT(*) FROM entities;
```

---

## Troubleshooting

**Frontend not loading?**
```bash
docker-compose logs frontend
# Look for npm install errors
```

**OAuth fails?**
```bash
# Check redirect URI matches EXACTLY in Google Console and .env
# Must be: http://localhost:8000/api/v1/auth/google/callback
```

**No emails syncing?**
```bash
# Check Celery worker
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker
```

**spaCy model missing?**
```bash
docker-compose exec backend python -m spacy download en_core_web_sm
docker-compose restart backend celery-worker
```

---

## Architecture Overview

```
Frontend (React)           Backend (FastAPI)         Workers
    :5173          →           :8000          →      Celery
      ↓                          ↓                      ↓
  User clicks              OAuth flow            Email sync
  "Connect"           →    Store tokens    →    Extract entities
      ↓                          ↓                      ↓
  Redirect to             Trigger sync           Store in DB
  Google                       ↓                      ↓
      ↓                   PostgreSQL  ←────────  Redis Queue
  Approve                 (messages,              (task queue)
      ↓                   entities)
  Return to
  Dashboard
```

---

## What Happens After Connection

1. **Backend** stores OAuth tokens (encrypted)
2. **Celery task** `sync_gmail_account(user_id, days=30)` starts
3. **Gmail API** fetches last 30 days of emails (batches of 100)
4. **Messages** stored in `messages` table
5. **Celery tasks** `extract_entities_from_message(msg_id)` × N
6. **spaCy + Regex** extract people, companies, amounts
7. **Entities** stored in `entities` table with deduplication
8. **Dashboard** shows results (auto-refresh every 5 sec)

**Timeline:**
- 100 emails = ~30 seconds to fetch
- 100 emails = ~2 minutes to extract entities
- Total: ~3 minutes for 100 emails

---

## Next Steps

✅ **Phase 1 MVP Complete!**

**Optional Enhancements:**
- [ ] Add Alembic migrations: `docker-compose exec backend alembic revision --autogenerate -m "Initial"`
- [ ] Add JWT authentication middleware
- [ ] Create graph visualization (Phase 2)
- [ ] Add Outlook integration
- [ ] Deploy to production

**Test API:**
```bash
# Get all entities
curl http://localhost:8000/api/v1/entities?limit=10

# Get people only
curl http://localhost:8000/api/v1/entities?entity_type=PERSON

# Get messages
curl http://localhost:8000/api/v1/messages?limit=5

# Get stats
curl http://localhost:8000/api/v1/messages/stats/summary
```

---

## Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Main UI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Flower | http://localhost:5555 | Celery monitor |
| PgAdmin | (optional) | Database admin |

**Logs:**
```bash
docker-compose logs -f backend      # API logs
docker-compose logs -f celery-worker # Sync logs
docker-compose logs -f frontend     # React logs
```

**Stop all:**
```bash
docker-compose down
```

**Reset everything:**
```bash
docker-compose down -v  # ⚠️ Deletes all data
```
