# msg2act Implementation Plan
## Knowledge Graph Platform for Personal Data Management

---

## Executive Summary

This plan outlines the phased development of a knowledge graph platform that ingests data from multiple sources (email, messaging, documents), extracts entities and relationships, and enables intelligent automation. The implementation follows a crawl-walk-run approach, starting with core Gmail integration and basic entity extraction (MVP), then expanding to advanced features.

**Timeline Approach:** Phased implementation with clear milestones
**Starting Point:** Greenfield project - all components to be built
**First Milestone:** Basic Gmail integration with entity extraction

---

## Technical Architecture

### Technology Stack (Recommended)

#### Backend
- **Framework:** Python FastAPI (async, high performance, easy OAuth integration)
- **Database:** PostgreSQL (relational data + JSONB for flexible entity storage)
- **Graph Database:** Neo4j or NetworkX (for relationship mapping and graph queries)
- **Vector Database:** Pinecone or Weaviate (for semantic search)
- **Task Queue:** Celery + Redis (background processing for email sync, extraction)
- **Cache:** Redis (session storage, rate limiting, caching)

#### NLP & AI
- **Entity Extraction:** spaCy (fast, production-ready) + Custom NER models
- **LLM Integration:** OpenAI GPT-4 or Anthropic Claude (for complex extraction, form filling)
- **Document Processing:** PyPDF2, pdfplumber, python-docx, Tesseract (OCR)
- **Speech-to-Text:** Whisper API or AssemblyAI

#### Frontend
- **Framework:** React + TypeScript
- **UI Library:** Tailwind CSS + shadcn/ui
- **State Management:** React Query + Zustand
- **Graph Visualization:** D3.js or vis.js or react-force-graph

#### Authentication & Security
- **OAuth 2.0:** Google OAuth Library, Microsoft MSAL
- **JWT:** PyJWT for token management
- **Encryption:** cryptography library (AES-256)
- **SSL/TLS:** Let's Encrypt certificates

#### DevOps & Deployment
- **Containerization:** Docker + Docker Compose
- **Orchestration:** Kubernetes (for production scale)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │Dashboard │ Graph    │ Search   │ Flows    │ Settings │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                   API Layer (FastAPI)                       │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  Auth    │Ingestion │Extraction│  Graph   │  Flows   │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────┬──────────┬─────────┬──────────┬────────────┬─────────┘
      │          │         │          │            │
┌─────▼────┐ ┌──▼─────┐ ┌─▼──────┐ ┌─▼────────┐ ┌─▼─────────┐
│PostgreSQL│ │ Redis  │ │ Neo4j  │ │Weaviate  │ │  Celery   │
│(Primary) │ │(Cache) │ │(Graph) │ │(Vectors) │ │(Tasks)    │
└──────────┘ └────────┘ └────────┘ └──────────┘ └───────────┘
                │
        ┌───────┴────────┐
        │  External APIs │
        ├────────────────┤
        │ - Gmail API    │
        │ - Outlook API  │
        │ - Slack API    │
        │ - WhatsApp API │
        │ - OpenAI API   │
        └────────────────┘
```

---

## Implementation Phases

## **PHASE 0: Project Foundation**
### Duration: Week 1
### Goal: Set up development environment and core infrastructure

#### Milestones
- [ ] Project repository structure created
- [ ] Development environment containerized (Docker Compose)
- [ ] CI/CD pipeline configured
- [ ] Database schemas designed
- [ ] API skeleton with health checks

#### Tasks

**0.1 Project Structure**
```
msg2act/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── ingestion.py
│   │   │   │   ├── entities.py
│   │   │   │   └── graph.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── gmail_service.py
│   │   │   ├── extraction_service.py
│   │   │   └── graph_service.py
│   │   ├── tasks/
│   │   └── utils/
│   ├── tests/
│   ├── alembic/  # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

**0.2 Database Schema Design**

*PostgreSQL Tables:*
- `users` - User accounts
- `oauth_tokens` - OAuth credentials (encrypted)
- `data_sources` - Connected services (Gmail, Slack, etc.)
- `messages` - Emails and messages
- `documents` - Uploaded/synced documents
- `entities` - Extracted entities (people, companies, amounts, dates)
- `relationships` - Entity relationships
- `extraction_jobs` - Tracking extraction tasks
- `sync_status` - Source sync metadata

**0.3 Docker Compose Setup**
```yaml
services:
  - postgres:14
  - redis:7
  - neo4j:latest
  - backend (FastAPI)
  - celery-worker
  - frontend (React dev server)
```

**0.4 Environment Configuration**
- Google OAuth credentials
- Database connection strings
- Redis connection
- JWT secret keys
- Encryption keys
- API rate limits

**Deliverables:**
- ✅ Running local development environment
- ✅ Database migrations framework
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Basic authentication endpoints
- ✅ Health check endpoints

---

## **PHASE 1: MVP - Gmail Integration + Basic Entity Extraction**
### Duration: Weeks 2-4
### Goal: Core value delivery - connect Gmail and extract key entities

This phase delivers the foundational user story:
*"As a user, I can connect my Gmail account and see people, companies, and amounts automatically extracted from my emails."*

#### Features (from Requirements)
- ✅ 1.1 Email Integration - Gmail
- ✅ 2.1 People Extraction
- ✅ 2.2 Company/Organization Extraction
- ✅ 2.3 Financial Amount Extraction (basic)
- ✅ 8.1 Global Semantic Search (basic)
- ✅ 10.1 Data Encryption

#### Milestones
- [ ] Gmail OAuth flow complete
- [ ] Historical email import working
- [ ] Real-time sync operational
- [ ] Entity extraction pipeline functional
- [ ] Basic search working
- [ ] Simple dashboard showing extracted entities

#### Tasks

**1.1 Gmail OAuth Integration**
- Implement Google OAuth 2.0 flow
- Store encrypted tokens in database
- Token refresh mechanism
- Scope: `gmail.readonly`, `gmail.modify` (for labeling)
- Handle OAuth errors and re-authentication

**1.2 Email Ingestion Service**
```python
# Key functions to implement:
- authenticate_gmail()
- fetch_historical_emails(days=30/90/365/all)
- sync_new_emails()  # Real-time sync
- parse_email_metadata()
- extract_email_body()
- handle_attachments()
- preserve_thread_grouping()
```

**1.3 Email Storage Schema**
```sql
messages (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  source_id UUID REFERENCES data_sources,
  message_id VARCHAR,  -- Gmail message ID
  thread_id VARCHAR,
  subject TEXT,
  from_email VARCHAR,
  from_name VARCHAR,
  to_emails JSONB,
  cc_emails JSONB,
  bcc_emails JSONB,
  body_text TEXT,
  body_html TEXT,
  received_at TIMESTAMP,
  labels JSONB,
  has_attachments BOOLEAN,
  raw_metadata JSONB,
  created_at TIMESTAMP
)
```

**1.4 Entity Extraction Pipeline**

*1.4.1 People Extraction*
- Use spaCy NER for PERSON entities
- Extract from: email addresses, signatures, body text
- Parse email signatures for structured data
- Deduplication logic:
  ```python
  # Match criteria:
  - Exact name match
  - Email domain match
  - Fuzzy name similarity (Levenshtein distance)
  - Manual merge capability
  ```

*1.4.2 Company Extraction*
- spaCy NER for ORG entities
- Email domain extraction (@company.com → Company Inc.)
- Signature parsing for company names
- Enrich with public data (Clearbit, LinkedIn) if available

*1.4.3 Financial Amount Extraction*
- Regex patterns for currency amounts:
  ```python
  patterns = [
    r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
    r'USD\s*\d+',
    r'€\d+',
    r'£\d+',
    r'₹\d+',
    # ... more patterns
  ]
  ```
- Currency detection
- Context extraction (who owes whom)
- Link to associated people/companies

*1.4.4 Entity Storage Schema*
```sql
entities (
  id UUID PRIMARY KEY,
  user_id UUID,
  type VARCHAR,  -- PERSON, COMPANY, AMOUNT, DATE
  name VARCHAR,
  normalized_name VARCHAR,  -- for deduplication
  attributes JSONB,  -- flexible storage
  confidence_score FLOAT,
  source_count INT,  -- how many sources mention this
  first_seen TIMESTAMP,
  last_seen TIMESTAMP,
  created_at TIMESTAMP
)

entity_mentions (
  id UUID PRIMARY KEY,
  entity_id UUID REFERENCES entities,
  message_id UUID REFERENCES messages,
  context TEXT,  -- surrounding text
  position INT,
  created_at TIMESTAMP
)
```

**1.5 Background Processing**
- Celery tasks for async processing:
  ```python
  @celery_app.task
  def sync_gmail_account(user_id, since_date):
      # Fetch emails
      # Queue extraction jobs

  @celery_app.task
  def extract_entities_from_message(message_id):
      # NLP processing
      # Entity creation/updating
      # Relationship detection
  ```

**1.6 Basic Search**
- Full-text search on messages (PostgreSQL FTS)
- Entity filtering
- Date range filtering
- Source filtering (by email sender)

**1.7 Simple Dashboard UI**
- Connection status widget
- Recent emails list
- Extracted entities (grouped by type):
  - People list with contact count
  - Companies list
  - Financial amounts timeline
- Basic search bar
- Entity detail modal

**1.8 Data Encryption**
- Encrypt OAuth tokens at rest (AES-256)
- Encrypt email content (optional, for sensitive data)
- TLS for all API calls

#### API Endpoints
```
POST   /api/v1/auth/google/connect
GET    /api/v1/auth/google/callback
POST   /api/v1/gmail/sync
GET    /api/v1/gmail/status
GET    /api/v1/messages
GET    /api/v1/messages/{id}
GET    /api/v1/entities
GET    /api/v1/entities/{id}
POST   /api/v1/entities/{id}/merge
GET    /api/v1/search
```

#### Testing Requirements
- Unit tests for extraction algorithms
- Integration tests for Gmail API
- Test deduplication logic
- Test OAuth flow (mock Google responses)
- Load test: 10,000 emails processed

#### Success Metrics
- ✅ User can connect Gmail in < 1 minute
- ✅ 1,000 emails processed in < 5 minutes
- ✅ Entity extraction accuracy > 85%
- ✅ Search results < 500ms
- ✅ Zero plaintext token storage

---

## **PHASE 2: Relationship Mapping + Graph Visualization**
### Duration: Weeks 5-6
### Goal: Show connections between entities in an interactive graph

#### Features (from Requirements)
- ✅ 3.1 Automatic Relationship Discovery
- ✅ 3.2 Manual Relationship Editing
- ✅ 3.3 Relationship Timeline
- ✅ 7.1 Interactive Graph Canvas
- ✅ 7.2 Graph Filtering
- ✅ 7.3 Entity Detail Panel
- ✅ 7.4 Path Finding

#### Tasks

**2.1 Relationship Detection**
```python
# Automatic relationships:
- Person → works_at → Company (from email signature)
- Person → knows → Person (co-mentioned in emails)
- Person → sent_email → Person
- Document → from → Person/Company
- Amount → paid_to/paid_by → Person/Company
```

**2.2 Neo4j Graph Storage**
```cypher
// Node types
(:Person {id, name, email, ...})
(:Company {id, name, domain, ...})
(:Amount {id, value, currency, ...})
(:Message {id, subject, date, ...})

// Relationships
(:Person)-[:WORKS_AT]->(:Company)
(:Person)-[:KNOWS {strength, first_contact, last_contact}]->(:Person)
(:Person)-[:SENT {date}]->(:Message)
(:Message)-[:MENTIONS]->(:Person|:Company|:Amount)
(:Amount)-[:PAID_BY]->(:Person|:Company)
```

**2.3 Relationship Strength Algorithm**
```python
strength = (
  interaction_count * 0.4 +
  recency_score * 0.3 +  # More recent = higher
  response_rate * 0.2 +
  thread_depth * 0.1
)
```

**2.4 Graph Visualization (Frontend)**
- Use D3.js force-directed graph or react-force-graph
- Node sizing by importance (connection count)
- Edge thickness by relationship strength
- Color coding by entity type
- Pan, zoom, drag interactions
- Click node → detail panel
- Hover → highlight connected nodes

**2.5 Path Finding Algorithm**
- Implement shortest path between two entities
- Neo4j Cypher query:
  ```cypher
  MATCH path = shortestPath(
    (a:Person {id: $person1_id})-[*]-(b:Person {id: $person2_id})
  )
  RETURN path
  ```

**2.6 Manual Relationship Editing**
- UI to add custom relationships
- Edit relationship type/label
- Add notes to relationships
- Delete incorrect relationships

#### Deliverables
- ✅ Interactive graph visualization
- ✅ Relationship timeline view
- ✅ Path finder between entities
- ✅ Manual relationship editor

---

## **PHASE 3: Multi-Source Expansion**
### Duration: Weeks 7-9
### Goal: Add Outlook, document uploads, and attachment processing

#### Features (from Requirements)
- ✅ 1.1 Outlook/Microsoft 365 Integration
- ✅ 1.4 Document Sources - Manual Upload
- ✅ 1.4 Google Drive/Dropbox (optional)
- ✅ 2.4 Date & Deadline Extraction
- ✅ 2.5 Document Classification

#### Tasks

**3.1 Outlook Integration**
- Microsoft OAuth (MSAL)
- Fetch emails via Microsoft Graph API
- Calendar events sync
- Reuse existing extraction pipeline

**3.2 Document Upload**
- Drag-and-drop UI
- Support: PDF, DOCX, XLSX, images
- Batch upload
- Progress indicators
- Document parsing:
  - PDF text extraction (PyPDF2, pdfplumber)
  - OCR for scanned PDFs (Tesseract)
  - Word/Excel parsing (python-docx, openpyxl)

**3.3 Attachment Processing**
- Extract attachments from Gmail/Outlook
- Store in object storage (S3 or local)
- Apply same parsing logic as uploads
- Link attachments to parent message

**3.4 Document Classification**
- Rule-based classification:
  - Invoice: "Invoice #", "Amount Due", "Payment Terms"
  - Contract: "Agreement", "Party A", "Effective Date"
  - Receipt: "Receipt", "Transaction ID"
  - Policy: "Policy Number", "Coverage"
- LLM-based classification (GPT-4) for ambiguous docs
- Confidence scores
- Manual override

**3.5 Date & Deadline Extraction**
- Extract absolute dates: "December 25, 2024", "2024-12-25"
- Resolve relative dates: "next Friday", "in 2 weeks"
- Context classification:
  - Payment due date
  - Contract expiry
  - Meeting date
  - Task deadline
- Store in structured format:
  ```sql
  deadlines (
    id UUID,
    entity_id UUID,  -- associated document/message
    deadline_type VARCHAR,
    deadline_date DATE,
    urgency VARCHAR,  -- high/medium/low
    completed BOOLEAN
  )
  ```

#### Deliverables
- ✅ Outlook connection working
- ✅ Document upload functional
- ✅ Attachments auto-processed
- ✅ Document types classified
- ✅ Deadlines extracted and stored

---

## **PHASE 4: Timeline & Deadline Tracking**
### Duration: Weeks 10-11
### Goal: Calendar view and deadline alerts

#### Features (from Requirements)
- ✅ 4.1 Unified Calendar View
- ✅ 4.2 Deadline Alerts
- ✅ 4.3 Auto-Detected Renewals
- ✅ 4.4 Calendar Sync (Google/Outlook)

#### Tasks

**4.1 Calendar UI**
- Month/week/day views
- Color-coded events by type
- Click event → source document
- Filters by event type, entity

**4.2 Alert System**
- Background job checking upcoming deadlines
- Configurable alert timing (1d, 3d, 1w before)
- In-app notifications
- Email notifications
- Push notifications (if mobile app exists)

**4.3 Renewal Detection**
- Pattern recognition for recurring events
- Annual/monthly patterns
- Link to policy documents
- Cost tracking

**4.4 Calendar Sync**
- Create events in Google Calendar
- Two-way sync option
- Conflict detection
- Event metadata includes source link

#### Deliverables
- ✅ Calendar view functional
- ✅ Alert notifications working
- ✅ Renewal patterns detected
- ✅ Google Calendar sync enabled

---

## **PHASE 5: Advanced Extraction & Corrections**
### Duration: Weeks 12-13
### Goal: Improve extraction accuracy and enable user corrections

#### Features (from Requirements)
- ✅ 2.3 Financial Amount Extraction (advanced - invoices)
- ✅ 2.6 Extraction Corrections
- ✅ 1.5 Connection Health Dashboard

#### Tasks

**5.1 Advanced Invoice Processing**
- Structured data extraction from invoices:
  - Invoice number
  - Invoice date
  - Due date
  - Line items
  - Subtotal, tax, total
  - Payer/payee details
- Use LLM (GPT-4 vision) for complex layouts
- Running totals: what I owe, what's owed to me

**5.2 Extraction Correction UI**
- Edit entity name, type, attributes
- Merge duplicate entities (drag & drop)
- Split incorrectly merged entities
- Delete false positives
- Correction feedback loop:
  - Store corrections in training data
  - Fine-tune extraction models
  - Improve future accuracy

**5.3 Connection Health Dashboard**
- All connected accounts listed
- Status indicators:
  - ✅ Connected
  - 🔄 Syncing
  - ⚠️ Error
  - ⏰ Token Expired
- Last sync timestamp
- One-click reconnect
- Error messages with resolution steps

#### Deliverables
- ✅ Invoice extraction > 90% accuracy
- ✅ User correction interface
- ✅ Connection health dashboard
- ✅ Model improvement from corrections

---

## **PHASE 6: Messaging Apps (WhatsApp, Slack)**
### Duration: Weeks 14-16
### Goal: Expand beyond email to messaging platforms

#### Features (from Requirements)
- ✅ 1.2 WhatsApp Integration
- ✅ 1.2 Slack Integration

#### Tasks

**6.1 WhatsApp Business API**
- WhatsApp Business account setup
- Message ingestion
- Media extraction (images, voice notes, docs)
- Contact name resolution
- Group chat support
- Participant tracking

**6.2 Slack Integration**
- Slack OAuth
- Workspace permissions
- Channel selection (configurable)
- DM ingestion
- File attachments
- Thread context preservation
- Reaction and emoji context

**6.3 Message Normalization**
- Unified message schema across sources
- Thread/conversation grouping
- Contact merging across platforms
- Cross-platform search

#### Deliverables
- ✅ WhatsApp messages synced
- ✅ Slack workspace connected
- ✅ Unified message view
- ✅ Cross-platform search

---

## **PHASE 7: Voice Notes & Transcription**
### Duration: Week 17
### Goal: Audio transcription and searchability

#### Features (from Requirements)
- ✅ 1.3 Voice Notes

#### Tasks

**7.1 Audio Upload**
- Support: MP3, M4A, WAV, OGG
- File size limits (e.g., 100MB)
- Progress indicator

**7.2 Speech-to-Text**
- Whisper API or AssemblyAI integration
- Speaker diarization (who said what)
- Timestamps per segment
- Store transcript as searchable text

**7.3 Entity Extraction from Transcripts**
- Apply same NLP pipeline to transcripts
- Link entities to audio timestamp
- Action item detection

#### Deliverables
- ✅ Voice note upload working
- ✅ Transcription accurate
- ✅ Transcripts searchable
- ✅ Entities extracted from audio

---

## **PHASE 8: Automated Action Flows**
### Duration: Weeks 18-20
### Goal: Enable workflow automation

#### Features (from Requirements)
- ✅ 5.1 Flow Templates
- ✅ 5.2 Custom Flow Builder
- ✅ 5.3 Approval Workflows
- ✅ 5.4 Flow History & Debugging
- ✅ 5.5 Connected Actions

#### Tasks

**8.1 Flow Engine**
- Workflow execution engine
- Trigger system:
  - Event-based (new document, deadline approaching)
  - Schedule-based (daily, weekly)
  - Manual trigger
- Condition evaluation
- Action execution

**8.2 Flow Templates**
- Pre-built templates:
  - Invoice Payment Reminder
  - Document Review Workflow
  - Meeting Scheduler
  - Expense Report Generation
  - Contract Renewal Alert
  - Follow-up Reminder
- One-click activation
- Customization before activation

**8.3 Visual Flow Builder**
- Drag-and-drop UI
- Nodes: Trigger, Condition, Action, Approval
- Connection lines showing flow
- Test flow functionality
- Version control for flows

**8.4 Approval Workflows**
- Pause flow for human approval
- Mobile-friendly approval UI
- Approve/reject with notes
- Timeout handling
- Audit log

**8.5 Connected Actions**
- Email draft creation (Gmail, Outlook API)
- Calendar event creation
- Task creation (Todoist, Notion, Asana APIs)
- Payment initiation (prepare data for Revolut, Wise)
- Webhook for custom integrations

**8.6 Flow Execution History**
- List of all runs (success, failed, pending)
- Detailed execution log
- Error debugging
- Retry mechanism
- Pause/resume controls

#### Deliverables
- ✅ Flow execution engine
- ✅ 6 pre-built templates
- ✅ Visual flow builder
- ✅ Approval system
- ✅ 5 connected actions

---

## **PHASE 9: Form Filling Automation**
### Duration: Weeks 21-22
### Goal: AI-powered form filling

#### Features (from Requirements)
- ✅ 6.1 Template-Based Form Filling
- ✅ 6.2 AI-Powered Form Detection
- ✅ 6.3 Form Preview & Edit
- ✅ 6.4 Export Options

#### Tasks

**9.1 Form Template Builder**
- Upload PDF/image form
- Define fillable fields
- Map fields to entity attributes
- Save template
- Template versioning
- Template library

**9.2 AI Form Detection**
- Upload any form
- GPT-4 Vision to detect fields
- Auto-suggest data from knowledge graph
- Confidence scores per field
- Manual correction interface

**9.3 Form Filling UI**
- Visual preview
- Inline field editing
- Highlight AI-filled vs manual
- Undo/redo
- Save draft

**9.4 Export**
- PDF download (flattened or form-fillable)
- Print-ready format
- Email directly
- Save to Drive/Dropbox
- Form generation history

#### Deliverables
- ✅ Template-based filling working
- ✅ AI form detection functional
- ✅ Preview & edit UI
- ✅ Multiple export formats

---

## **PHASE 10: Advanced Search & Discovery**
### Duration: Week 23
### Goal: Semantic search and smart suggestions

#### Features (from Requirements)
- ✅ 8.2 Faceted Search Results
- ✅ 8.3 Saved Searches
- ✅ 8.4 Smart Suggestions

#### Tasks

**10.1 Semantic Search**
- Vector embeddings for all content (OpenAI embeddings)
- Store in Weaviate or Pinecone
- Natural language queries
- Semantic similarity search
- Hybrid search (keyword + semantic)

**10.2 Faceted Search**
- Filter by: entity type, document type, date range, source
- Filter counts
- Multiple filters combinable
- Clear all filters

**10.3 Saved Searches**
- Save query with custom name
- Quick access from dashboard
- Edit/delete saved searches
- Export query

**10.4 Smart Suggestions**
- "Related to what you're viewing"
- "You might have forgotten" (old pending items)
- "Coming up soon" (upcoming deadlines)
- Personalized based on usage patterns

#### Deliverables
- ✅ Semantic search < 500ms
- ✅ Faceted filtering
- ✅ Saved searches
- ✅ Smart suggestions algorithm

---

## **PHASE 11: Alerts & Notifications**
### Duration: Week 24
### Goal: Comprehensive notification system

#### Features (from Requirements)
- ✅ 9.1 Configurable Alert Rules
- ✅ 9.2 Notification Center
- ✅ 9.3 Daily/Weekly Digest
- ✅ 9.4 Mobile Push Notifications

#### Tasks

**11.1 Alert Rule Builder**
- When [condition], alert me via [channel]
- Conditions: new entity, amount > threshold, deadline, keyword
- Channels: in-app, email, push, SMS
- Test rule before saving

**11.2 Notification Center**
- Notification bell with unread count
- List view (read/unread)
- Mark as read, archive, delete
- Click → navigate to source
- Bulk actions

**11.3 Digest Emails**
- Daily/weekly configurable
- Summary of: new entities, deadlines, completed actions, pending approvals
- HTML email template
- One-click access to dashboard

**11.4 Mobile Push Notifications**
- Push notification service (Firebase, OneSignal)
- Notification categories
- Do not disturb schedule
- Quick actions from notification

#### Deliverables
- ✅ Custom alert rules
- ✅ Notification center
- ✅ Digest emails
- ✅ Push notifications

---

## **PHASE 12: Privacy, Security & Compliance**
### Duration: Week 25
### Goal: Enterprise-grade security and compliance

#### Features (from Requirements)
- ✅ 10.2 Access Control
- ✅ 10.3 Data Export
- ✅ 10.4 Data Deletion
- ✅ 10.5 Consent Management
- ✅ 10.6 Audit Trail

#### Tasks

**12.1 Access Control (Team Features)**
- Role-based access control (RBAC)
- Roles: Admin, Member, Viewer
- Granular permissions per data source
- Team workspace isolation
- Activity log

**12.2 Data Export**
- Full export (JSON, CSV)
- Graph export (GraphML format)
- Document download (ZIP)
- Secure download link
- GDPR compliance (30-day delivery)

**12.3 Data Deletion**
- Delete individual entities/documents
- Delete service data
- Full account deletion (30-day grace)
- Confirmation flow
- Deletion from backups (90 days)

**12.4 Consent Management**
- Granular consent per source
- Pause/resume ingestion
- Revoke service access
- Consent history
- Audit log

**12.5 Audit Trail**
- Log all data access
- Log all modifications
- Log all exports
- Searchable audit log
- Export audit log for compliance

#### Deliverables
- ✅ RBAC implemented
- ✅ Data export functional
- ✅ Deletion workflows
- ✅ Consent management
- ✅ Audit logging

---

## **PHASE 13: Graph Enhancements & Clustering**
### Duration: Week 26
### Goal: Advanced graph features

#### Features (from Requirements)
- ✅ 7.5 Graph Clustering

#### Tasks

**13.1 Auto-Clustering**
- Community detection algorithms (Louvain, Label Propagation)
- Cluster by: company, project, time period
- Cluster labels
- Expand/collapse clusters
- Custom cluster creation

**13.2 Graph Layout Algorithms**
- Force-directed layout
- Hierarchical layout
- Circular layout
- User preference saved

#### Deliverables
- ✅ Auto-clustering
- ✅ Multiple layout options
- ✅ Custom clusters

---

## **PHASE 14: Polish & Performance Optimization**
### Duration: Week 27
### Goal: Production-ready system

#### Tasks

**14.1 Performance Optimization**
- Database query optimization
- Indexing strategy
- Caching frequently accessed data
- Lazy loading in UI
- Pagination for large datasets
- Background job optimization

**14.2 Error Handling**
- Graceful error messages
- Retry logic for failed syncs
- Error reporting to monitoring
- User-friendly error pages

**14.3 Documentation**
- User guide
- API documentation
- Admin documentation
- Video tutorials
- FAQ

**14.4 Testing**
- End-to-end tests
- Load testing (10K users)
- Security testing (OWASP)
- Accessibility testing (WCAG)

**14.5 Deployment**
- Production infrastructure setup
- SSL certificates
- CDN for static assets
- Database backups
- Monitoring & alerts
- Logging

#### Deliverables
- ✅ < 2s page load times
- ✅ 99.9% uptime
- ✅ Complete documentation
- ✅ Production deployment

---

## Feature-to-Pricing Tier Mapping

### Personal Tier ($15/mo) - Phases 1-5
- Gmail/Outlook connection
- Basic entity extraction (people, companies, amounts)
- Graph visualization
- Search
- 5 active action flows
- Data encryption
- Manual uploads

### Pro Tier ($49/mo) - Phases 1-11
- All Personal features
- WhatsApp/Slack integration
- Voice transcription
- Advanced extraction (invoices, contracts)
- Unlimited action flows
- Form filling
- Smart suggestions
- Priority support

### Business Tier ($499/mo) - Phases 1-14
- All Pro features
- Team sharing & collaboration
- Role-based access control
- API access
- Audit trail
- Data export
- Dedicated account manager
- SLA guarantees

---

## Critical Dependencies & Risks

### External API Dependencies
- **Gmail API** - Rate limits (250 quota units/user/second)
- **Outlook API** - Throttling limits
- **OpenAI API** - Cost and rate limits
- **Whisper API** - Audio transcription costs

### Technical Risks
1. **Extraction Accuracy** - May require custom model training
2. **Scalability** - Large email volumes (100K+ emails)
3. **Real-time Sync** - Gmail push notifications complexity
4. **Graph Performance** - Large graphs (10K+ nodes) may slow down
5. **Cost** - LLM API costs can scale quickly

### Mitigation Strategies
- Implement aggressive caching
- Batch processing for non-urgent tasks
- Use smaller models where possible (spaCy vs GPT)
- Progressive loading for large graphs
- Rate limiting and quota monitoring

---

## Success Metrics (KPIs)

### MVP (Phase 1)
- ✅ 100 beta users onboarded
- ✅ 85%+ entity extraction accuracy
- ✅ < 5 min to process 1,000 emails
- ✅ < 500ms search response time

### Post-Launch (Phase 14)
- ✅ 1,000 paying users
- ✅ 90%+ entity extraction accuracy
- ✅ 99.9% uptime
- ✅ < 2s average page load
- ✅ Net Promoter Score (NPS) > 50

---

## Development Resources Required

### Team (Recommended)
- 1 Backend Engineer (Python/FastAPI)
- 1 Frontend Engineer (React/TypeScript)
- 1 ML/NLP Engineer (spaCy, LLM integration)
- 1 DevOps Engineer (part-time)
- 1 Product Designer (UI/UX)
- 1 QA Engineer

### Infrastructure Costs (Monthly Estimates)
- Cloud hosting (AWS/GCP): $500-1,000
- Database (PostgreSQL, Neo4j): $200-500
- Redis cache: $50-100
- OpenAI API: $500-2,000 (depending on usage)
- Email service (SendGrid): $50
- Monitoring (Datadog): $100
- **Total: ~$1,500-4,000/month**

---

## Next Steps

### Immediate Actions (Week 1)
1. ✅ Set up GitHub repository
2. ✅ Configure development environment (Docker Compose)
3. ✅ Create Google Cloud project for OAuth
4. ✅ Design database schemas
5. ✅ Set up CI/CD pipeline
6. ✅ Create project documentation

### Phase 1 Kickoff (Week 2)
1. Implement Gmail OAuth flow
2. Build email ingestion service
3. Set up Celery for background tasks
4. Implement basic entity extraction
5. Create simple dashboard UI

---

## Conclusion

This implementation plan provides a structured roadmap from MVP (basic Gmail integration + entity extraction) to a full-featured knowledge graph platform. The phased approach allows for:

1. **Early value delivery** - Users see value in Phase 1
2. **Iterative feedback** - Learn from users at each phase
3. **Risk mitigation** - Technical challenges addressed incrementally
4. **Resource efficiency** - Build only what's validated

**Estimated Total Timeline:** 27 weeks (~6.5 months) for complete platform

**MVP Timeline:** 4 weeks to first working product

**Recommended Approach:** Start with Phase 1 (MVP), validate with beta users, then proceed to subsequent phases based on user feedback and prioritization.
