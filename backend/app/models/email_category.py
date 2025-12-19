"""
Email Category model for user-defined email classifications
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmailCategory(Base):
    """
    User-defined email categories (Invoice, Flight, Insurance, etc.)
    """
    __tablename__ = "email_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Category info
    name = Column(String, nullable=False)  # "Invoice", "Flight Booking", "Insurance"
    description = Column(Text, nullable=True)  # User description for LLM
    color = Column(String, default="#3B82F6")  # Hex color for UI
    icon = Column(String, nullable=True)  # Icon name/emoji

    # LLM detection
    is_auto_detect = Column(Boolean, default=True)  # Enable LLM auto-tagging
    detection_prompt = Column(Text, nullable=True)  # Custom LLM prompt

    # Examples for few-shot learning
    example_subjects = Column(JSONB, nullable=True)  # ["Invoice #123", "Your invoice from..."]
    example_patterns = Column(JSONB, nullable=True)  # Regex patterns, keywords

    # Default category (system-provided)
    is_default = Column(Boolean, default=False)
    is_urgent_category = Column(Boolean, default=False)  # Flag urgent emails

    # Stats
    tagged_count = Column(Integer, default=0)  # How many emails tagged

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="email_categories")
    tags = relationship("EmailTag", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EmailCategory {self.name}>"


class EmailTag(Base):
    """
    Tags applied to messages (linking messages to categories)
    """
    __tablename__ = "email_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("email_categories.id"), nullable=False, index=True)

    # Tagging metadata
    confidence = Column(Float, default=0.0)  # LLM confidence (0-1)
    is_auto_tagged = Column(Boolean, default=False)  # Auto vs manual tag
    is_confirmed = Column(Boolean, default=False)  # User confirmed the tag

    # Extracted fields (category-specific data)
    extracted_data = Column(JSONB, nullable=True)
    # Examples:
    # Invoice: {"invoice_number": "INV-123", "amount": 1500, "due_date": "2024-12-31"}
    # Flight: {"flight_number": "AA123", "departure": "2024-12-25", "destination": "NYC"}
    # Insurance: {"policy_number": "POL-456", "renewal_date": "2025-01-01"}

    # Urgency detection
    is_urgent = Column(Boolean, default=False)
    urgency_reason = Column(Text, nullable=True)  # Why it's urgent

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    message = relationship("Message", backref="tags")
    category = relationship("EmailCategory", back_populates="tags")

    def __repr__(self):
        return f"<EmailTag message={self.message_id} category={self.category_id}>"
