# Workflow System - Email Categorization & Automation

## Overview

The workflow system allows users to:
1. **Create custom categories** (Invoice, Flight, Insurance, etc.)
2. **Auto-tag emails** using LLM classification
3. **Build automation flows** (If Invoice → Save to Google Sheets)
4. **Extract structured data** from emails
5. **Detect urgent emails** automatically

---

## Quick Start

### 1. Initialize Default Categories

```bash
curl -X POST "http://localhost:8000/api/v1/categories/init-defaults?user_id=USER_ID"
```

**Creates 8 default categories:**
- 💵 Invoice
- 🧾 Receipt
- ✈️ Flight
- 🏨 Hotel
- 📦 Shipping
- 📅 Meeting
- 🛡️ Insurance
- 🚨 Urgent

### 2. Create Custom Category

```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "name": "Property Tax",
    "description": "Property tax bills and assessments",
    "color": "#8B5CF6",
    "icon": "🏠",
    "is_auto_detect": true,
    "example_subjects": ["Property Tax Notice", "Tax Assessment"]
  }'
```

### 3. Auto-Classify Email

```bash
curl -X POST "http://localhost:8000/api/v1/messages/MESSAGE_ID/classify?user_id=USER_ID"
```

**Response:**
```json
{
  "suggestions": [
    {
      "category_id": "uuid",
      "category_name": "Invoice",
      "confidence": 0.95,
      "is_urgent": true,
      "urgency_reason": "Payment due in 3 days",
      "extracted_data": {
        "invoice_number": "INV-2024-001",
        "amount": 1500,
        "currency": "USD",
        "due_date": "2024-12-31"
      }
    }
  ]
}
```

### 4. Apply Tag (Manual or Auto)

```bash
curl -X POST "http://localhost:8000/api/v1/messages/MESSAGE_ID/tag" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "CATEGORY_ID",
    "is_auto_tagged": false,
    "confidence": 1.0,
    "extracted_data": {
      "invoice_number": "INV-123",
      "amount": 1500
    }
  }'
```

### 5. Create Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "name": "Save Invoices to Google Sheets",
    "trigger_type": "category_match",
    "trigger_config": {
      "category_id": "INVOICE_CATEGORY_ID"
    },
    "actions": [
      {
        "type": "save_to_sheet",
        "config": {
          "sheet_id": "GOOGLE_SHEET_ID",
          "fields": ["invoice_number", "amount", "due_date"]
        }
      },
      {
        "type": "send_notification",
        "config": {
          "email": "user@example.com",
          "template": "invoice_alert"
        }
      }
    ],
    "require_approval": false,
    "auto_execute": true
  }'
```

---

## Database Schema

### EmailCategory
```sql
- id: UUID
- user_id: UUID
- name: "Invoice"
- description: "Bills and payment requests"
- color: "#EF4444"
- icon: "💵"
- is_auto_detect: true
- example_subjects: ["Invoice #...", "Payment due"]
- is_default: false
- is_urgent_category: false
- tagged_count: 45
```

### EmailTag
```sql
- id: UUID
- message_id: UUID
- category_id: UUID
- confidence: 0.95
- is_auto_tagged: true
- is_confirmed: false
- extracted_data: {"invoice_number": "INV-123", "amount": 1500}
- is_urgent: true
- urgency_reason: "Payment due in 3 days"
```

### Workflow
```sql
- id: UUID
- user_id: UUID
- name: "Save Invoices to Sheets"
- trigger_type: "category_match"
- trigger_config: {"category_id": "uuid"}
- actions: [{type: "save_to_sheet", config: {...}}]
- require_approval: false
- execution_count: 23
- success_count: 22
- failure_count: 1
```

### WorkflowExecution
```sql
- id: UUID
- workflow_id: UUID
- message_id: UUID
- status: "success" | "failed" | "pending" | "pending_approval"
- results: {"saved_to_sheet": true, "row_id": 123}
- error_message: null
```

---

## API Endpoints

### Categories

```
POST   /api/v1/categories/init-defaults     # Create default categories
GET    /api/v1/categories                   # List all categories
POST   /api/v1/categories                   # Create category
PUT    /api/v1/categories/{id}              # Update category
DELETE /api/v1/categories/{id}              # Delete category
```

### Tagging

```
POST   /api/v1/messages/{id}/classify       # LLM classify email
POST   /api/v1/messages/{id}/tag            # Apply tag
GET    /api/v1/messages/tagged              # Get tagged messages
```

### Workflows

```
GET    /api/v1/workflows                    # List workflows
POST   /api/v1/workflows                    # Create workflow
PUT    /api/v1/workflows/{id}               # Update workflow
DELETE /api/v1/workflows/{id}               # Delete workflow
GET    /api/v1/workflows/{id}/executions    # Execution history
POST   /api/v1/workflows/{id}/test          # Test workflow
POST   /api/v1/workflows/executions/{id}/approve  # Approve execution
```

---

## Workflow Actions

### 1. Save to Google Sheets
```json
{
  "type": "save_to_sheet",
  "config": {
    "sheet_id": "spreadsheet-id",
    "fields": ["invoice_number", "amount", "due_date", "vendor"]
  }
}
```

### 2. Send Notification
```json
{
  "type": "send_notification",
  "config": {
    "email": "user@example.com",
    "template": "invoice_alert"
  }
}
```

### 3. Add to Calendar
```json
{
  "type": "add_to_calendar",
  "config": {
    "calendar_id": "primary",
    "event_type": "payment_due"
  }
}
```

### 4. Forward Email
```json
{
  "type": "forward_email",
  "config": {
    "forward_to": "accountant@company.com"
  }
}
```

---

## Use Cases

### Invoice Management
1. **Auto-detect** invoices with LLM
2. **Extract** invoice number, amount, due date
3. **Save** to Google Sheets for tracking
4. **Notify** before due date
5. **Flag** urgent if due soon

### Flight Tracking
1. **Detect** flight bookings
2. **Extract** flight number, dates, airports
3. **Add** to Google Calendar
4. **Send** reminder 24h before

### Insurance Renewals
1. **Detect** insurance emails
2. **Extract** policy number, renewal date
3. **Alert** 30 days before renewal
4. **Track** in spreadsheet

### Meeting Coordination
1. **Detect** meeting invites
2. **Extract** date, time, link, attendees
3. **Auto-add** to calendar
4. **Send** reminder notification

---

## LLM Classification

### How It Works

1. **User creates category** with description & examples
2. **New email arrives** → Celery task triggers
3. **LLM analyzes** email against all categories
4. **Returns** confidence scores + extracted data
5. **Auto-tags** if confidence > 0.5
6. **User confirms** or edits tags
7. **Workflow triggers** on confirmed tags

### Classification Prompt Example

```
You are an email classification assistant.

Available Categories:
- Invoice: Bills, payment requests
- Flight: Flight bookings, boarding passes

Email:
Subject: Your Invoice #2024-001
Body: Payment of $1,500 is due by Dec 31...

Task: Classify and extract structured data.

Return:
{
  "classifications": [{
    "category_name": "Invoice",
    "confidence": 0.98,
    "is_urgent": true,
    "extracted_data": {
      "invoice_number": "2024-001",
      "amount": 1500,
      "due_date": "2024-12-31"
    }
  }]
}
```

---

## Default Tag Generation

Generate tags for emails without custom categories:

```bash
# LLM suggests common tags
curl -X POST "http://localhost:8000/api/v1/messages/MESSAGE_ID/classify"
```

**Response:**
```json
{
  "tags": ["Invoice", "Urgent"],
  "urgency_level": "high",
  "action_required": true,
  "summary": "Invoice payment due in 3 days"
}
```

---

## Workflow Execution Flow

```
1. Email arrives
   ↓
2. Entity extraction (existing)
   ↓
3. LLM classification
   ↓
4. Tag applied (auto or manual)
   ↓
5. Check for matching workflows
   ↓
6. If match → Execute actions
   ↓
7. If require_approval → Pause
   ↓
8. User approves → Continue
   ↓
9. Actions execute (save to sheet, notify, etc.)
   ↓
10. Log execution results
```

---

## Configuration

### Enable OpenAI for LLM

```env
# .env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4-turbo-preview
```

### Google Sheets Integration (Future)

```env
GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json
```

---

## Example Workflow: Complete Invoice Pipeline

```json
{
  "name": "Complete Invoice Processing",
  "trigger_type": "category_match",
  "trigger_config": {"category_id": "INVOICE_CATEGORY_ID"},
  "actions": [
    {
      "type": "save_to_sheet",
      "config": {
        "sheet_id": "INVOICE_TRACKER_ID",
        "fields": ["invoice_number", "vendor", "amount", "due_date", "status"]
      }
    },
    {
      "type": "add_to_calendar",
      "config": {
        "calendar_id": "primary",
        "event_type": "payment_due",
        "reminder_days": 3
      }
    },
    {
      "type": "send_notification",
      "config": {
        "email": "finance@company.com",
        "subject": "New Invoice: {invoice_number}",
        "body": "Invoice {invoice_number} for ${amount} due on {due_date}"
      }
    }
  ],
  "require_approval": false,
  "auto_execute": true
}
```

---

## Next Steps

**Implemented:**
- ✅ Database models
- ✅ LLM classification service
- ✅ Category/tag API endpoints
- ✅ Workflow execution engine
- ✅ Default categories

**Coming Soon:**
- [ ] Frontend UI for category management
- [ ] Workflow visual builder
- [ ] Google Sheets integration
- [ ] Google Calendar integration
- [ ] Email notification service
- [ ] Celery task for auto-classification

**Future Enhancements:**
- [ ] Multi-language support
- [ ] Custom extraction rules
- [ ] Workflow versioning
- [ ] A/B testing for prompts
- [ ] Batch tagging
- [ ] Tag confidence feedback loop
