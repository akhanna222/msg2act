"""
Celery tasks for email ingestion and synchronization
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.oauth_token import OAuthToken
from app.models.data_source import DataSource
from app.models.message import Message
from app.services.gmail_service import GmailService
from app.tasks import celery_app


@celery_app.task(name="sync_gmail_account")
def sync_gmail_account(user_id: str, historical_days: int = 30):
    """
    Sync Gmail account for a user

    Args:
        user_id: UUID of the user
        historical_days: Number of days to sync historically
    """
    db = SessionLocal()

    try:
        # Get user
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            print(f"User {user_id} not found")
            return

        # Get OAuth token
        oauth_token = (
            db.query(OAuthToken)
            .filter(
                OAuthToken.user_id == user.id,
                OAuthToken.provider == "google",
            )
            .first()
        )

        if not oauth_token:
            print(f"No Google OAuth token found for user {user_id}")
            return

        # Get data source
        data_source = (
            db.query(DataSource)
            .filter(
                DataSource.user_id == user.id,
                DataSource.source_type == "gmail",
            )
            .first()
        )

        if not data_source:
            print(f"No Gmail data source found for user {user_id}")
            return

        # Update data source status
        data_source.status = "syncing"
        db.commit()

        # Create Gmail service
        gmail_service = GmailService(oauth_token)

        # Calculate date range
        after_date = datetime.utcnow() - timedelta(days=historical_days)

        # Fetch messages
        print(f"Fetching Gmail messages for user {user_id} (after {after_date})")
        messages = gmail_service.fetch_messages(
            max_results=500,  # Fetch in batches
            after_date=after_date,
        )

        print(f"Fetched {len(messages)} messages")

        # Store messages in database
        new_count = 0
        for msg_data in messages:
            # Check if message already exists
            existing = (
                db.query(Message)
                .filter(
                    Message.user_id == user.id,
                    Message.external_id == msg_data["external_id"],
                )
                .first()
            )

            if existing:
                continue  # Skip duplicates

            # Create new message
            message = Message(
                user_id=user.id,
                source_id=data_source.id,
                external_id=msg_data["external_id"],
                thread_id=msg_data.get("thread_id"),
                subject=msg_data.get("subject"),
                from_email=msg_data.get("from_email"),
                from_name=msg_data.get("from_name"),
                to_emails=msg_data.get("to_emails"),
                cc_emails=msg_data.get("cc_emails"),
                body_text=msg_data.get("body_text"),
                body_html=msg_data.get("body_html"),
                received_at=msg_data.get("received_at"),
                has_attachments=msg_data.get("has_attachments", False),
                labels=msg_data.get("labels"),
                raw_metadata=msg_data.get("raw_metadata"),
                is_processed=False,
            )

            db.add(message)
            new_count += 1

            # Commit in batches
            if new_count % 50 == 0:
                db.commit()

        db.commit()

        # Update data source
        data_source.status = "connected"
        data_source.last_sync_at = datetime.utcnow()
        data_source.total_items_synced += new_count
        data_source.last_item_count = new_count
        db.commit()

        print(f"Synced {new_count} new messages for user {user_id}")

        # Queue extraction tasks for new messages
        if new_count > 0:
            from app.tasks.extraction_tasks import extract_entities_from_message

            # Get unprocessed messages
            unprocessed = (
                db.query(Message)
                .filter(
                    Message.user_id == user.id,
                    Message.is_processed == False,
                )
                .limit(100)  # Process in batches
                .all()
            )

            for message in unprocessed:
                extract_entities_from_message.delay(str(message.id))

        return {"synced": new_count, "total": len(messages)}

    except Exception as e:
        print(f"Error syncing Gmail for user {user_id}: {e}")

        if data_source:
            data_source.status = "error"
            data_source.error_message = str(e)
            data_source.error_count += 1
            data_source.last_error_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()


@celery_app.task(name="sync_all_gmail_accounts")
def sync_all_gmail_accounts():
    """
    Periodic task to sync all active Gmail accounts
    """
    db = SessionLocal()

    try:
        # Get all active Gmail data sources
        data_sources = (
            db.query(DataSource)
            .filter(
                DataSource.source_type == "gmail",
                DataSource.is_active == True,
                DataSource.sync_enabled == True,
            )
            .all()
        )

        print(f"Found {len(data_sources)} active Gmail accounts to sync")

        for source in data_sources:
            # Queue sync task for each user
            sync_gmail_account.delay(str(source.user_id), historical_days=7)  # Sync last 7 days

    except Exception as e:
        print(f"Error in sync_all_gmail_accounts: {e}")

    finally:
        db.close()
