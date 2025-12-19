"""
Message model for storing emails and messages from various sources
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)

    # External message identifiers (Gmail message ID, Slack message TS, etc.)
    external_id = Column(String, nullable=False, index=True)
    thread_id = Column(String, nullable=True, index=True)

    # Message metadata
    subject = Column(Text, nullable=True)
    from_email = Column(String, nullable=True, index=True)
    from_name = Column(String, nullable=True)

    # Recipients (stored as JSONB arrays)
    to_emails = Column(JSONB, nullable=True)  # ["email1@example.com", "email2@example.com"]
    cc_emails = Column(JSONB, nullable=True)
    bcc_emails = Column(JSONB, nullable=True)

    # Message content
    body_text = Column(Text, nullable=True)  # Plain text version
    body_html = Column(Text, nullable=True)  # HTML version

    # Message timing
    received_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)

    # Message properties
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)

    # Labels/categories (Gmail labels, Outlook categories, etc.)
    labels = Column(JSONB, nullable=True)  # ["INBOX", "IMPORTANT", "CATEGORY_PERSONAL"]

    # Raw metadata from the source (for debugging and additional data)
    raw_metadata = Column(JSONB, nullable=True)

    # Processing status
    is_processed = Column(Boolean, default=False)  # Entity extraction completed
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="messages")
    data_source = relationship("DataSource", back_populates="messages")
    entity_mentions = relationship("EntityMention", back_populates="message", cascade="all, delete-orphan")

    # Create composite index for efficient querying
    __table_args__ = (
        Index('idx_user_received', 'user_id', 'received_at'),
        Index('idx_user_thread', 'user_id', 'thread_id'),
        Index('idx_source_external', 'source_id', 'external_id'),
    )

    def __repr__(self):
        return f"<Message {self.subject[:50] if self.subject else 'No subject'}>"
