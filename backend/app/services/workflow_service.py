"""
Workflow execution service
Handles automation flows (If Invoice → Save to Google Sheets)
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution
from app.models.email_category import EmailTag
from app.models.message import Message


class WorkflowExecutionService:
    """
    Executes user-defined workflows
    """

    def __init__(self, db: Session):
        self.db = db

    def check_and_execute(self, message: Message, tag: EmailTag) -> Optional[WorkflowExecution]:
        """
        Check if any workflows should execute for this tagged message

        Args:
            message: The email message
            tag: The tag that was applied

        Returns:
            WorkflowExecution if workflow was triggered, else None
        """
        # Find workflows triggered by this category
        workflows = (
            self.db.query(Workflow)
            .filter(
                Workflow.user_id == message.user_id,
                Workflow.is_active == True,
                Workflow.trigger_type == "category_match",
            )
            .all()
        )

        for workflow in workflows:
            # Check if trigger matches
            if workflow.trigger_config.get("category_id") == str(tag.category_id):
                # Execute workflow
                return self.execute_workflow(workflow, message, tag)

        return None

    def execute_workflow(
        self, workflow: Workflow, message: Message, tag: EmailTag
    ) -> WorkflowExecution:
        """
        Execute a workflow

        Args:
            workflow: Workflow to execute
            message: Message that triggered it
            tag: Tag associated with the message

        Returns:
            WorkflowExecution record
        """
        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            message_id=message.id,
            status="running" if workflow.auto_execute else "pending",
            requires_approval=workflow.require_approval,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # If requires approval, pause here
        if workflow.require_approval:
            execution.status = "pending_approval"
            self.db.commit()
            return execution

        # Execute actions
        results = {}
        try:
            for action in workflow.actions:
                action_type = action.get("type")
                action_config = action.get("config", {})

                if action_type == "save_to_sheet":
                    result = self._action_save_to_sheet(message, tag, action_config)
                    results["save_to_sheet"] = result

                elif action_type == "send_notification":
                    result = self._action_send_notification(message, tag, action_config)
                    results["send_notification"] = result

                elif action_type == "add_to_calendar":
                    result = self._action_add_to_calendar(message, tag, action_config)
                    results["add_to_calendar"] = result

                elif action_type == "forward_email":
                    result = self._action_forward_email(message, action_config)
                    results["forward_email"] = result

            # Mark as success
            execution.status = "success"
            execution.results = results
            execution.completed_at = datetime.utcnow()

            # Update workflow stats
            workflow.execution_count += 1
            workflow.success_count += 1
            workflow.last_executed_at = datetime.utcnow()

        except Exception as e:
            # Mark as failed
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            # Update workflow stats
            workflow.execution_count += 1
            workflow.failure_count += 1

        self.db.commit()
        return execution

    def _action_save_to_sheet(
        self, message: Message, tag: EmailTag, config: Dict
    ) -> Dict:
        """
        Save extracted data to Google Sheets

        Args:
            message: The email message
            tag: Tag with extracted data
            config: Action configuration

        Returns:
            Result dict
        """
        # TODO: Implement Google Sheets API integration
        # For now, return mock success

        sheet_id = config.get("sheet_id")
        fields = config.get("fields", [])

        # Prepare row data from extracted_data
        row_data = []
        for field in fields:
            value = tag.extracted_data.get(field) if tag.extracted_data else None
            row_data.append(value)

        # Mock: Would append to Google Sheets here
        # from googleapiclient.discovery import build
        # service = build('sheets', 'v4', credentials=creds)
        # result = service.spreadsheets().values().append(...).execute()

        return {
            "success": True,
            "sheet_id": sheet_id,
            "row_data": row_data,
            "message": "Data would be saved to Google Sheets (integration pending)",
        }

    def _action_send_notification(
        self, message: Message, tag: EmailTag, config: Dict
    ) -> Dict:
        """
        Send notification (email/SMS/push)

        Args:
            message: The email message
            tag: Tag data
            config: Notification config

        Returns:
            Result dict
        """
        # TODO: Implement notification service
        # For now, log the notification

        recipient = config.get("email")
        template = config.get("template")

        notification_text = f"""
        New {tag.category.name} detected!
        Subject: {message.subject}
        From: {message.from_email}
        """

        print(f"NOTIFICATION: Would send to {recipient}: {notification_text}")

        return {
            "success": True,
            "recipient": recipient,
            "message": "Notification would be sent (integration pending)",
        }

    def _action_add_to_calendar(
        self, message: Message, tag: EmailTag, config: Dict
    ) -> Dict:
        """
        Add event to Google Calendar

        Args:
            message: The email message
            tag: Tag with extracted data
            config: Calendar config

        Returns:
            Result dict
        """
        # TODO: Implement Google Calendar API integration

        calendar_id = config.get("calendar_id", "primary")

        # Extract meeting details from tag.extracted_data
        meeting_date = tag.extracted_data.get("meeting_date") if tag.extracted_data else None
        meeting_time = tag.extracted_data.get("meeting_time") if tag.extracted_data else None

        print(f"CALENDAR: Would add event on {meeting_date} at {meeting_time}")

        return {
            "success": True,
            "calendar_id": calendar_id,
            "message": "Event would be added to calendar (integration pending)",
        }

    def _action_forward_email(self, message: Message, config: Dict) -> Dict:
        """
        Forward email to another address

        Args:
            message: The email to forward
            config: Forward config

        Returns:
            Result dict
        """
        # TODO: Implement email forwarding

        forward_to = config.get("forward_to")

        print(f"FORWARD: Would forward email to {forward_to}")

        return {
            "success": True,
            "forward_to": forward_to,
            "message": "Email would be forwarded (integration pending)",
        }
