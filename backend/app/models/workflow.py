"""
Workflow models for email automation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Workflow(Base):
    """
    User-defined automation workflows
    Example: "If Invoice → Save to Google Sheets"
    """
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Workflow info
    name = Column(String, nullable=False)  # "Save Invoices to Sheets"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Trigger conditions (when to execute)
    trigger_type = Column(String, default="category_match")
    # Types: "category_match", "keyword_match", "sender_match", "manual"

    trigger_config = Column(JSONB, nullable=False)
    # Examples:
    # category_match: {"category_id": "uuid"}
    # keyword_match: {"keywords": ["invoice", "payment due"]}
    # sender_match: {"email": "billing@company.com"}

    # Actions to perform (what to do)
    actions = Column(JSONB, nullable=False)
    # Array of actions:
    # [
    #   {
    #     "type": "save_to_sheet",
    #     "config": {
    #       "sheet_id": "xxx",
    #       "fields": ["invoice_number", "amount", "due_date"]
    #     }
    #   },
    #   {
    #     "type": "send_notification",
    #     "config": {"email": "user@example.com", "template": "invoice_alert"}
    #   }
    # ]

    # Execution settings
    require_approval = Column(Boolean, default=False)  # Pause for user approval
    auto_execute = Column(Boolean, default=True)

    # Stats
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow {self.name}>"


class WorkflowExecution(Base):
    """
    Log of workflow executions
    """
    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)

    # Execution status
    status = Column(String, default="pending")  # pending, running, success, failed, cancelled
    error_message = Column(Text, nullable=True)

    # Execution results
    results = Column(JSONB, nullable=True)
    # Example: {"saved_to_sheet": true, "row_id": 123, "notification_sent": true}

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    message = relationship("Message", backref="workflow_executions")

    def __repr__(self):
        return f"<WorkflowExecution {self.id} status={self.status}>"
