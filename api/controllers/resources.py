from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from ..models import models


def create(db: Session, resource):
    # Create a new Resource object with the data the client sent
    db_resource = models.Resource(
        item=resource.item,
        amount=resource.amount
    )
    try:
        # Add it to the session and save it to the database
        db.add(db_resource)
        db.commit()
    except IntegrityError as e:
        # Undo the failed save, then tell the client what went wrong
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Resource could not be created: the item name must be unique") from e
    # Reload the object so it includes the new id
    db.refresh(db_resource)
    return db_resource


def read_all(db: Session):
    # Get every row in the resources table
    return db.query(models.Resource).all()


def read_one(db: Session, resource_id):
    # Get the one row whose id matches (or None if there isn't one)
    return db.query(models.Resource).filter(models.Resource.id == resource_id).first()


def update(db: Session, resource_id, resource):
    # Find the row to update
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id)
    # Only include the fields the client actually sent
    update_data = resource.model_dump(exclude_unset=True)
    if update_data:
        try:
            db_resource.update(update_data, synchronize_session=False)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Resource could not be updated: the item name must be unique") from e
    # Return the updated row
    return db_resource.first()


def delete(db: Session, resource_id):
    # Find the row to delete
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id)
    try:
        db_resource.delete(synchronize_session=False)
        db.commit()
    except IntegrityError as e:
        # Happens if a recipe still uses this resource
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Resource cannot be deleted because other records still reference it") from e
    # 204 means "success, nothing to send back"
    return Response(status_code=status.HTTP_204_NO_CONTENT)