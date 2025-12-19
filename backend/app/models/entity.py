"""
Entity model for storing extracted entities (people, companies, amounts, dates, etc.)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Entity type (PERSON, COMPANY, AMOUNT, DATE, LOCATION, etc.)
    entity_type = Column(String, nullable=False, index=True)

    # Entity identification
    name = Column(String, nullable=False)  # Display name
    normalized_name = Column(String, nullable=False, index=True)  # Lowercase, normalized for deduplication

    # Attributes (flexible JSONB storage for type-specific data)
    # Examples:
    # PERSON: {"email": "john@example.com", "phone": "+1234567890", "title": "CEO"}
    # COMPANY: {"domain": "example.com", "industry": "Technology", "website": "https://example.com"}
    # AMOUNT: {"value": 1500.00, "currency": "USD"}
    # DATE: {"date": "2024-12-25", "type": "deadline", "context": "Payment due"}
    attributes = Column(JSONB, nullable=True)

    # Confidence score (0.0 to 1.0)
    confidence_score = Column(Float, default=0.0)

    # Metadata
    source_count = Column(Integer, default=1)  # Number of sources that mention this entity
    mention_count = Column(Integer, default=0)  # Total number of mentions across all messages

    # Temporal tracking
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Manual corrections/verifications
    is_verified = Column(Boolean, default=False)  # User has verified this entity
    is_merged = Column(Boolean, default=False)  # This entity was merged into another
    merged_into_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="entities")
    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")

    # Self-referential relationship for merged entities
    merged_into = relationship("Entity", remote_side=[id], foreign_keys=[merged_into_id])

    # Create composite indexes
    __table_args__ = (
        Index('idx_user_type', 'user_id', 'entity_type'),
        Index('idx_user_normalized', 'user_id', 'normalized_name'),
    )

    def __repr__(self):
        return f"<Entity {self.entity_type}: {self.name}>"


class EntityMention(Base):
    """
    Represents a mention of an entity in a specific message
    """
    __tablename__ = "entity_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)

    # Context of the mention
    context = Column(Text, nullable=True)  # Surrounding text
    position = Column(Integer, nullable=True)  # Character position in message
    confidence = Column(Float, default=0.0)  # Confidence of this specific mention

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    entity = relationship("Entity", back_populates="mentions")
    message = relationship("Message", back_populates="entity_mentions")

    # Composite index
    __table_args__ = (
        Index('idx_entity_message', 'entity_id', 'message_id'),
    )

    def __repr__(self):
        return f"<EntityMention entity={self.entity_id} in message={self.message_id}>"
