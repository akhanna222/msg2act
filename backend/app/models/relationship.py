"""
Relationship model for storing connections between entities
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship as orm_relationship

from app.core.database import Base


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source and target entities
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)

    # Relationship type
    # Examples:
    # - PERSON -> WORKS_AT -> COMPANY
    # - PERSON -> KNOWS -> PERSON
    # - PERSON -> SENT_EMAIL -> PERSON
    # - DOCUMENT -> FROM -> COMPANY
    # - AMOUNT -> PAID_BY -> PERSON
    relationship_type = Column(String, nullable=False, index=True)

    # Relationship strength (0.0 to 1.0)
    # Calculated based on interaction frequency, recency, etc.
    strength = Column(Float, default=0.0)

    # Interaction metadata
    interaction_count = Column(Integer, default=0)
    first_interaction = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, nullable=True)

    # Additional attributes (flexible storage)
    # Examples:
    # - For WORKS_AT: {"title": "CEO", "department": "Engineering"}
    # - For SENT_EMAIL: {"thread_count": 5, "response_rate": 0.8}
    attributes = Column(JSONB, nullable=True)

    # Notes (user-added context)
    notes = Column(Text, nullable=True)

    # Manual relationship flag
    is_manual = Column(Boolean, default=False)  # User manually created this

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite indexes
    __table_args__ = (
        Index('idx_source_target', 'source_entity_id', 'target_entity_id'),
        Index('idx_target_source', 'target_entity_id', 'source_entity_id'),
        Index('idx_relationship_type', 'relationship_type'),
    )

    def __repr__(self):
        return f"<Relationship {self.source_entity_id} -{self.relationship_type}-> {self.target_entity_id}>"
