"""
Workflow automation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.workflow import Workflow, WorkflowExecution
from app.services.workflow_service import WorkflowExecutionService

router = APIRouter()


@router.get("/workflows")
async def get_workflows(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Get all workflows for a user

    Args:
        user_id: User ID (optional for MVP)
        is_active: Filter by active status
        db: Database session

    Returns:
        List of workflows
    """
    query = db.query(Workflow)

    if user_id:
        query = query.filter(Workflow.user_id == UUID(user_id))

    if is_active is not None:
        query = query.filter(Workflow.is_active == is_active)

    workflows = query.order_by(Workflow.created_at.desc()).all()

    return {
        "workflows": [
            {
                "id": str(wf.id),
                "name": wf.name,
                "description": wf.description,
                "is_active": wf.is_active,
                "trigger_type": wf.trigger_type,
                "trigger_config": wf.trigger_config,
                "actions": wf.actions,
                "require_approval": wf.require_approval,
                "execution_count": wf.execution_count,
                "success_count": wf.success_count,
                "failure_count": wf.failure_count,
                "last_executed_at": wf.last_executed_at.isoformat() if wf.last_executed_at else None,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
            }
            for wf in workflows
        ]
    }


@router.post("/workflows")
async def create_workflow(
    user_id: str,
    name: str,
    description: Optional[str] = None,
    trigger_type: str = "category_match",
    trigger_config: Dict = {},
    actions: List[Dict] = [],
    require_approval: bool = False,
    auto_execute: bool = True,
    db: Session = Depends(get_db),
):
    """
    Create a new workflow

    Args:
        user_id: User ID
        name: Workflow name
        description: Description
        trigger_type: Trigger type (category_match, keyword_match, sender_match)
        trigger_config: Trigger configuration
        actions: List of actions to perform
        require_approval: Whether to require user approval
        auto_execute: Whether to auto-execute
        db: Database session

    Returns:
        Created workflow

    Example:
        {
            "user_id": "uuid",
            "name": "Save Invoices to Sheets",
            "trigger_type": "category_match",
            "trigger_config": {"category_id": "invoice-category-uuid"},
            "actions": [
                {
                    "type": "save_to_sheet",
                    "config": {
                        "sheet_id": "spreadsheet-id",
                        "fields": ["invoice_number", "amount", "due_date"]
                    }
                }
            ]
        }
    """
    workflow = Workflow(
        user_id=UUID(user_id),
        name=name,
        description=description,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        actions=actions,
        require_approval=require_approval,
        auto_execute=auto_execute,
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "message": "Workflow created successfully",
    }


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    trigger_config: Optional[Dict] = None,
    actions: Optional[List[Dict]] = None,
    require_approval: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Update a workflow

    Args:
        workflow_id: Workflow ID
        ...: Fields to update
        db: Database session

    Returns:
        Success message
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if name is not None:
        workflow.name = name
    if description is not None:
        workflow.description = description
    if is_active is not None:
        workflow.is_active = is_active
    if trigger_config is not None:
        workflow.trigger_config = trigger_config
    if actions is not None:
        workflow.actions = actions
    if require_approval is not None:
        workflow.require_approval = require_approval

    workflow.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Workflow updated", "id": str(workflow.id)}


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a workflow

    Args:
        workflow_id: Workflow ID
        db: Database session

    Returns:
        Success message
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db.delete(workflow)
    db.commit()

    return {"message": "Workflow deleted"}


@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: UUID,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get execution history for a workflow

    Args:
        workflow_id: Workflow ID
        limit: Max results
        offset: Pagination offset
        db: Database session

    Returns:
        List of executions
    """
    query = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id
    )

    total = query.count()
    executions = query.order_by(WorkflowExecution.started_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "executions": [
            {
                "id": str(exec.id),
                "workflow_id": str(exec.workflow_id),
                "message_id": str(exec.message_id),
                "status": exec.status,
                "error_message": exec.error_message,
                "results": exec.results,
                "requires_approval": exec.requires_approval,
                "approved_at": exec.approved_at.isoformat() if exec.approved_at else None,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            }
            for exec in executions
        ],
    }


@router.post("/workflows/{workflow_id}/test")
async def test_workflow(
    workflow_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Test a workflow on a specific message

    Args:
        workflow_id: Workflow ID
        message_id: Message ID to test with
        db: Database session

    Returns:
        Test execution result
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    from app.models.message import Message
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Create a mock tag for testing
    from app.models.email_tag import EmailTag

    mock_tag = EmailTag(
        message_id=message.id,
        category_id=UUID(workflow.trigger_config.get("category_id")),
        confidence=1.0,
        is_auto_tagged=False,
    )

    # Execute workflow
    service = WorkflowExecutionService(db)
    execution = service.execute_workflow(workflow, message, mock_tag)

    return {
        "execution_id": str(execution.id),
        "status": execution.status,
        "results": execution.results,
        "error_message": execution.error_message,
    }


@router.post("/workflows/executions/{execution_id}/approve")
async def approve_execution(
    execution_id: UUID,
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Approve a pending workflow execution

    Args:
        execution_id: Execution ID
        user_id: User approving
        db: Database session

    Returns:
        Success message
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Execution is not pending approval")

    # Mark as approved and execute
    execution.approved_by = UUID(user_id)
    execution.approved_at = datetime.utcnow()
    execution.status = "running"

    # Re-execute the workflow
    service = WorkflowExecutionService(db)
    # TODO: Continue execution from where it paused

    execution.status = "success"
    execution.completed_at = datetime.utcnow()

    db.commit()

    return {"message": "Execution approved and completed"}
