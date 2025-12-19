"""
Entity management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models.entity import Entity

router = APIRouter()


@router.get("/entities")
async def get_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get entities with optional filtering

    Args:
        entity_type: Filter by entity type (PERSON, COMPANY, AMOUNT, DATE)
        search: Search by name
        limit: Maximum number of results
        offset: Pagination offset
        db: Database session

    Returns:
        list: List of entities
    """
    query = db.query(Entity).filter(Entity.is_merged == False)

    if entity_type:
        query = query.filter(Entity.entity_type == entity_type.upper())

    if search:
        query = query.filter(Entity.name.ilike(f"%{search}%"))

    total = query.count()
    entities = query.order_by(Entity.mention_count.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "entities": [
            {
                "id": str(e.id),
                "type": e.entity_type,
                "name": e.name,
                "attributes": e.attributes,
                "confidence": e.confidence_score,
                "mentions": e.mention_count,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
            }
            for e in entities
        ],
    }


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific entity

    Args:
        entity_id: UUID of the entity
        db: Database session

    Returns:
        dict: Entity details including mentions
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get mentions with message context
    mentions = []
    for mention in entity.mentions[:10]:  # Limit to 10 recent mentions
        mentions.append({
            "message_id": str(mention.message_id),
            "context": mention.context,
            "confidence": mention.confidence,
            "created_at": mention.created_at.isoformat(),
        })

    return {
        "id": str(entity.id),
        "type": entity.entity_type,
        "name": entity.name,
        "attributes": entity.attributes,
        "confidence": entity.confidence_score,
        "source_count": entity.source_count,
        "mention_count": entity.mention_count,
        "first_seen": entity.first_seen.isoformat() if entity.first_seen else None,
        "last_seen": entity.last_seen.isoformat() if entity.last_seen else None,
        "is_verified": entity.is_verified,
        "mentions": mentions,
    }


@router.post("/entities/{entity_id}/merge")
async def merge_entities(
    entity_id: UUID,
    target_entity_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Merge one entity into another

    Args:
        entity_id: Entity to merge (will be marked as merged)
        target_entity_id: Target entity to merge into
        db: Database session

    Returns:
        dict: Success message
    """
    source_entity = db.query(Entity).filter(Entity.id == entity_id).first()
    target_entity = db.query(Entity).filter(Entity.id == target_entity_id).first()

    if not source_entity or not target_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if source_entity.user_id != target_entity.user_id:
        raise HTTPException(status_code=403, detail="Cannot merge entities from different users")

    # Mark source as merged
    source_entity.is_merged = True
    source_entity.merged_into_id = target_entity_id

    # Update target entity statistics
    target_entity.mention_count += source_entity.mention_count
    target_entity.source_count += source_entity.source_count

    # Update all mentions to point to target entity
    for mention in source_entity.mentions:
        mention.entity_id = target_entity_id

    db.commit()

    return {"message": "Entities merged successfully"}


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: UUID, db: Session = Depends(get_db)):
    """
    Delete an entity

    Args:
        entity_id: UUID of the entity to delete
        db: Database session

    Returns:
        dict: Success message
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db.delete(entity)
    db.commit()

    return {"message": "Entity deleted successfully"}
