"""
Data Source model for tracking connected services (Gmail, Outlook, Slack, etc.)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Source type (gmail, outlook, slack, whatsapp, drive, dropbox, manual_upload)
    source_type = Column(String, nullable=False, index=True)

    # Source name (user-friendly name)
    source_name = Column(String, nullable=True)

    # Connection status (connected, syncing, error, expired)
    status = Column(String, default="connected", nullable=False)

    # Sync configuration
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)

    # Sync metadata
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    sync_frequency_minutes = Column(Integer, default=5)

    # Historical sync settings (for email)
    historical_days = Column(Integer, default=30)  # 30, 90, 365, or -1 for all

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    last_error_at = Column(DateTime, nullable=True)

    # Provider-specific metadata
    metadata = Column(JSONB, nullable=True)  # Flexible storage for provider-specific data

    # Statistics
    total_items_synced = Column(Integer, default=0)
    last_item_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="data_sources")
    messages = relationship("Message", back_populates="data_source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource {self.source_type} for user {self.user_id}>"
