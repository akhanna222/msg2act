"""
Celery tasks for entity extraction
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.message import Message
from app.models.entity import Entity, EntityMention
from app.services.extraction_service import EntityExtractor
from app.tasks import celery_app


@celery_app.task(name="extract_entities_from_message")
def extract_entities_from_message(message_id: str):
    """
    Extract entities from a message

    Args:
        message_id: UUID of the message
    """
    db = SessionLocal()
    extractor = EntityExtractor()

    try:
        # Get message
        message = db.query(Message).filter(Message.id == UUID(message_id)).first()

        if not message:
            print(f"Message {message_id} not found")
            return

        if message.is_processed:
            print(f"Message {message_id} already processed")
            return

        # Combine subject and body for extraction
        text = ""
        if message.subject:
            text += message.subject + "\n\n"
        if message.body_text:
            text += message.body_text

        if not text.strip():
            # No content to extract from
            message.is_processed = True
            message.processed_at = datetime.utcnow()
            db.commit()
            return

        print(f"Extracting entities from message {message_id}")

        # Extract all entities
        extracted = extractor.extract_all(
            text,
            from_email=f"{message.from_name} <{message.from_email}>"
            if message.from_name
            else message.from_email,
        )

        # Process each entity type
        for entity_type, entities in extracted.items():
            for entity_data in entities:
                # Find or create entity
                entity = _find_or_create_entity(
                    db,
                    message.user_id,
                    entity_type.upper(),
                    entity_data["name"],
                    entity_data["normalized_name"],
                    entity_data["attributes"],
                    entity_data["confidence"],
                )

                # Create entity mention
                mention = EntityMention(
                    entity_id=entity.id,
                    message_id=message.id,
                    context=entity_data.get("context", "")[:500],  # Limit context length
                    confidence=entity_data["confidence"],
                )

                db.add(mention)

                # Update entity statistics
                entity.mention_count += 1
                entity.last_seen = datetime.utcnow()

        # Mark message as processed
        message.is_processed = True
        message.processed_at = datetime.utcnow()

        db.commit()

        print(f"Extracted entities from message {message_id}")

        return {"message_id": message_id, "status": "completed"}

    except Exception as e:
        print(f"Error extracting entities from message {message_id}: {e}")

        if message:
            message.processing_error = str(e)
            db.commit()

        raise

    finally:
        db.close()


def _find_or_create_entity(
    db: Session,
    user_id: UUID,
    entity_type: str,
    name: str,
    normalized_name: str,
    attributes: dict,
    confidence: float,
) -> Entity:
    """
    Find existing entity or create new one

    Args:
        db: Database session
        user_id: User ID
        entity_type: Type of entity (PERSON, COMPANY, AMOUNT, DATE)
        name: Display name
        normalized_name: Normalized name for matching
        attributes: Additional attributes
        confidence: Confidence score

    Returns:
        Entity instance
    """
    # Try to find existing entity
    existing = (
        db.query(Entity)
        .filter(
            Entity.user_id == user_id,
            Entity.entity_type == entity_type,
            Entity.normalized_name == normalized_name,
            Entity.is_merged == False,
        )
        .first()
    )

    if existing:
        # Update existing entity
        existing.source_count += 1

        # Merge attributes
        if attributes:
            if not existing.attributes:
                existing.attributes = {}

            for key, value in attributes.items():
                if key not in existing.attributes or not existing.attributes[key]:
                    existing.attributes[key] = value

        # Update confidence (average)
        existing.confidence_score = (existing.confidence_score + confidence) / 2

        db.commit()
        return existing

    # Create new entity
    entity = Entity(
        user_id=user_id,
        entity_type=entity_type,
        name=name,
        normalized_name=normalized_name,
        attributes=attributes or {},
        confidence_score=confidence,
        source_count=1,
        mention_count=0,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )

    db.add(entity)
    db.commit()
    db.refresh(entity)

    return entity


@celery_app.task(name="process_unprocessed_messages")
def process_unprocessed_messages():
    """
    Periodic task to process any unprocessed messages
    """
    db = SessionLocal()

    try:
        # Get unprocessed messages
        unprocessed = (
            db.query(Message)
            .filter(Message.is_processed == False, Message.processing_error == None)
            .limit(100)  # Process in batches
            .all()
        )

        print(f"Found {len(unprocessed)} unprocessed messages")

        for message in unprocessed:
            extract_entities_from_message.delay(str(message.id))

    except Exception as e:
        print(f"Error in process_unprocessed_messages: {e}")

    finally:
        db.close()
