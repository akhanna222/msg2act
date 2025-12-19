"""
OAuth Token model for storing encrypted OAuth credentials
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # OAuth provider (google, microsoft, etc.)
    provider = Column(String, nullable=False, index=True)

    # Encrypted tokens (using AES-256)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_type = Column(String, default="Bearer")

    # Token metadata
    expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)  # Space-separated scopes

    # Provider-specific user identifier (e.g., Google user ID)
    provider_user_id = Column(String, nullable=True)
    provider_email = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="oauth_tokens")

    def __repr__(self):
        return f"<OAuthToken {self.provider} for user {self.user_id}>"
