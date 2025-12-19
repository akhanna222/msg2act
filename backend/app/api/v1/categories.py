"""
Email category and tagging endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.email_category import EmailCategory, EmailTag
from app.models.message import Message
from app.services.classification_service import EmailClassificationService

router = APIRouter()


# Default categories to create for new users
DEFAULT_CATEGORIES = [
    {"name": "Invoice", "description": "Bills, invoices, payment requests", "color": "#EF4444", "icon": "💵"},
    {"name": "Receipt", "description": "Purchase receipts, confirmations", "color": "#10B981", "icon": "🧾"},
    {"name": "Flight", "description": "Flight bookings, boarding passes", "color": "#3B82F6", "icon": "✈️"},
    {"name": "Hotel", "description": "Hotel reservations, confirmations", "color": "#8B5CF6", "icon": "🏨"},
    {"name": "Shipping", "description": "Package tracking, delivery updates", "color": "#F59E0B", "icon": "📦"},
    {"name": "Meeting", "description": "Meeting invites, calendar events", "color": "#06B6D4", "icon": "📅"},
    {"name": "Insurance", "description": "Insurance policies, claims, renewals", "color": "#EC4899", "icon": "🛡️"},
    {"name": "Urgent", "description": "Urgent emails requiring immediate action", "color": "#DC2626", "icon": "🚨", "is_urgent_category": True},
]


@router.post("/categories/init-defaults")
async def init_default_categories(user_id: str, db: Session = Depends(get_db)):
    """
    Initialize default categories for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of created categories
    """
    created = []

    for cat_data in DEFAULT_CATEGORIES:
        # Check if already exists
        existing = (
            db.query(EmailCategory)
            .filter(
                EmailCategory.user_id == UUID(user_id),
                EmailCategory.name == cat_data["name"],
            )
            .first()
        )

        if not existing:
            category = EmailCategory(
                user_id=UUID(user_id),
                name=cat_data["name"],
                description=cat_data["description"],
                color=cat_data["color"],
                icon=cat_data.get("icon"),
                is_default=True,
                is_urgent_category=cat_data.get("is_urgent_category", False),
            )
            db.add(category)
            created.append(cat_data["name"])

    db.commit()

    return {"created": created, "total": len(created)}


@router.get("/categories")
async def get_categories(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get all categories for a user

    Args:
        user_id: User ID (optional for MVP)
        db: Database session

    Returns:
        List of categories
    """
    query = db.query(EmailCategory)

    if user_id:
        query = query.filter(EmailCategory.user_id == UUID(user_id))

    categories = query.order_by(EmailCategory.created_at.desc()).all()

    return {
        "categories": [
            {
                "id": str(cat.id),
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "icon": cat.icon,
                "is_auto_detect": cat.is_auto_detect,
                "is_default": cat.is_default,
                "is_urgent_category": cat.is_urgent_category,
                "tagged_count": cat.tagged_count,
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
            }
            for cat in categories
        ]
    }


@router.post("/categories")
async def create_category(
    user_id: str,
    name: str,
    description: Optional[str] = None,
    color: str = "#3B82F6",
    icon: Optional[str] = None,
    is_auto_detect: bool = True,
    example_subjects: Optional[List[str]] = None,
    db: Session = Depends(get_db),
):
    """
    Create a new custom category

    Args:
        user_id: User ID
        name: Category name
        description: Category description (used by LLM)
        color: Hex color
        icon: Icon/emoji
        is_auto_detect: Enable LLM auto-detection
        example_subjects: Example email subjects
        db: Database session

    Returns:
        Created category
    """
    category = EmailCategory(
        user_id=UUID(user_id),
        name=name,
        description=description,
        color=color,
        icon=icon,
        is_auto_detect=is_auto_detect,
        example_subjects=example_subjects or [],
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": str(category.id),
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "icon": category.icon,
        "is_auto_detect": category.is_auto_detect,
    }


@router.put("/categories/{category_id}")
async def update_category(
    category_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    is_auto_detect: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Update a category

    Args:
        category_id: Category ID
        ...: Fields to update
        db: Database session

    Returns:
        Updated category
    """
    category = db.query(EmailCategory).filter(EmailCategory.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if name is not None:
        category.name = name
    if description is not None:
        category.description = description
    if color is not None:
        category.color = color
    if icon is not None:
        category.icon = icon
    if is_auto_detect is not None:
        category.is_auto_detect = is_auto_detect

    category.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Category updated", "id": str(category.id)}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a category

    Args:
        category_id: Category ID
        db: Database session

    Returns:
        Success message
    """
    category = db.query(EmailCategory).filter(EmailCategory.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default category")

    db.delete(category)
    db.commit()

    return {"message": "Category deleted"}


@router.post("/messages/{message_id}/classify")
async def classify_message(
    message_id: UUID,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Classify a message using LLM

    Args:
        message_id: Message ID
        user_id: User ID (optional)
        db: Database session

    Returns:
        Suggested tags
    """
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get user's categories
    categories = (
        db.query(EmailCategory)
        .filter(
            EmailCategory.user_id == message.user_id,
            EmailCategory.is_auto_detect == True,
        )
        .all()
    )

    # Classify
    classifier = EmailClassificationService()
    classifications = classifier.classify_email(message, categories)

    return {"message_id": str(message_id), "suggestions": classifications}


@router.post("/messages/{message_id}/tag")
async def tag_message(
    message_id: UUID,
    category_id: UUID,
    is_auto_tagged: bool = False,
    confidence: float = 1.0,
    extracted_data: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """
    Apply a tag to a message

    Args:
        message_id: Message ID
        category_id: Category ID
        is_auto_tagged: Whether this was auto-tagged
        confidence: Confidence score
        extracted_data: Extracted structured data
        db: Database session

    Returns:
        Created tag
    """
    # Check if already tagged
    existing = (
        db.query(EmailTag)
        .filter(
            EmailTag.message_id == message_id,
            EmailTag.category_id == category_id,
        )
        .first()
    )

    if existing:
        return {"message": "Already tagged", "tag_id": str(existing.id)}

    # Create tag
    tag = EmailTag(
        message_id=message_id,
        category_id=category_id,
        is_auto_tagged=is_auto_tagged,
        confidence=confidence,
        is_confirmed=not is_auto_tagged,  # Manual tags are auto-confirmed
        extracted_data=extracted_data,
    )

    db.add(tag)

    # Update category stats
    category = db.query(EmailCategory).filter(EmailCategory.id == category_id).first()
    if category:
        category.tagged_count += 1

    db.commit()
    db.refresh(tag)

    return {
        "tag_id": str(tag.id),
        "message_id": str(message_id),
        "category_id": str(category_id),
    }


@router.get("/messages/tagged")
async def get_tagged_messages(
    category_id: Optional[UUID] = None,
    is_urgent: Optional[bool] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get tagged messages

    Args:
        category_id: Filter by category
        is_urgent: Filter by urgency
        limit: Max results
        offset: Pagination offset
        db: Database session

    Returns:
        Tagged messages
    """
    query = db.query(EmailTag).join(Message)

    if category_id:
        query = query.filter(EmailTag.category_id == category_id)

    if is_urgent is not None:
        query = query.filter(EmailTag.is_urgent == is_urgent)

    total = query.count()
    tags = query.order_by(Message.received_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "tags": [
            {
                "tag_id": str(tag.id),
                "message_id": str(tag.message_id),
                "category": {
                    "id": str(tag.category.id),
                    "name": tag.category.name,
                    "color": tag.category.color,
                    "icon": tag.category.icon,
                },
                "message": {
                    "subject": tag.message.subject,
                    "from_email": tag.message.from_email,
                    "received_at": tag.message.received_at.isoformat() if tag.message.received_at else None,
                },
                "confidence": tag.confidence,
                "is_auto_tagged": tag.is_auto_tagged,
                "is_urgent": tag.is_urgent,
                "extracted_data": tag.extracted_data,
            }
            for tag in tags
        ],
    }
