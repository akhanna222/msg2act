"""
Message endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.message import Message

router = APIRouter()


@router.get("/messages")
async def get_messages(
    source_type: Optional[str] = None,
    from_email: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get messages with optional filtering

    Args:
        source_type: Filter by source type (gmail, outlook, etc.)
        from_email: Filter by sender email
        search: Search in subject and body
        start_date: Filter messages after this date (ISO format)
        end_date: Filter messages before this date (ISO format)
        limit: Maximum number of results
        offset: Pagination offset
        db: Database session

    Returns:
        dict: List of messages
    """
    query = db.query(Message)

    # Apply filters
    if from_email:
        query = query.filter(Message.from_email == from_email)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Message.subject.ilike(search_term)) | (Message.body_text.ilike(search_term))
        )

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Message.received_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Message.received_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    total = query.count()
    messages = query.order_by(Message.received_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "messages": [
            {
                "id": str(m.id),
                "subject": m.subject,
                "from_email": m.from_email,
                "from_name": m.from_name,
                "to_emails": m.to_emails,
                "received_at": m.received_at.isoformat() if m.received_at else None,
                "has_attachments": m.has_attachments,
                "labels": m.labels,
                "is_processed": m.is_processed,
            }
            for m in messages
        ],
    }


@router.get("/messages/{message_id}")
async def get_message(message_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed message information

    Args:
        message_id: UUID of the message
        db: Database session

    Returns:
        dict: Full message details including body and extracted entities
    """
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get extracted entities from this message
    entities = []
    for mention in message.entity_mentions:
        entities.append({
            "entity_id": str(mention.entity_id),
            "entity_type": mention.entity.entity_type,
            "entity_name": mention.entity.name,
            "context": mention.context,
            "confidence": mention.confidence,
        })

    return {
        "id": str(message.id),
        "external_id": message.external_id,
        "thread_id": message.thread_id,
        "subject": message.subject,
        "from_email": message.from_email,
        "from_name": message.from_name,
        "to_emails": message.to_emails,
        "cc_emails": message.cc_emails,
        "body_text": message.body_text,
        "body_html": message.body_html,
        "received_at": message.received_at.isoformat() if message.received_at else None,
        "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        "has_attachments": message.has_attachments,
        "attachment_count": message.attachment_count,
        "labels": message.labels,
        "is_processed": message.is_processed,
        "entities": entities,
    }


@router.get("/messages/stats/summary")
async def get_message_stats(db: Session = Depends(get_db)):
    """
    Get message statistics

    Returns:
        dict: Statistics about messages
    """
    total_messages = db.query(Message).count()
    processed_messages = db.query(Message).filter(Message.is_processed == True).count()

    # Messages in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_messages = db.query(Message).filter(Message.received_at >= thirty_days_ago).count()

    return {
        "total_messages": total_messages,
        "processed_messages": processed_messages,
        "pending_processing": total_messages - processed_messages,
        "last_30_days": recent_messages,
    }
