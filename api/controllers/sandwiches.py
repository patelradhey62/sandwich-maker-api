from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from ..models import models


def create(db: Session, sandwich):
    # Create a new Sandwich object with the data the client sent
    db_sandwich = models.Sandwich(
        sandwich_name=sandwich.sandwich_name,
        price=sandwich.price
    )
    try:
        # Add it to the session and save it to the database
        db.add(db_sandwich)
        db.commit()
    except IntegrityError as e:
        # Undo the failed save, then tell the client what went wrong
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Sandwich could not be created: the sandwich name must be unique") from e
    # Reload the object so it includes the new id
    db.refresh(db_sandwich)
    return db_sandwich


def read_all(db: Session):
    # Get every row in the sandwiches table
    return db.query(models.Sandwich).all()


def read_one(db: Session, sandwich_id):
    # Get the one row whose id matches (or None if there isn't one)
    return db.query(models.Sandwich).filter(models.Sandwich.id == sandwich_id).first()


def update(db: Session, sandwich_id, sandwich):
    # Find the row to update
    db_sandwich = db.query(models.Sandwich).filter(models.Sandwich.id == sandwich_id)
    # Only include the fields the client actually sent
    update_data = sandwich.model_dump(exclude_unset=True)
    if update_data:
        try:
            db_sandwich.update(update_data, synchronize_session=False)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Sandwich could not be updated: the sandwich name must be unique") from e
    # Return the updated row
    return db_sandwich.first()


def delete(db: Session, sandwich_id):
    # Find the row to delete
    db_sandwich = db.query(models.Sandwich).filter(models.Sandwich.id == sandwich_id)
    try:
        db_sandwich.delete(synchronize_session=False)
        db.commit()
    except IntegrityError as e:
        # Happens if a recipe or order still uses this sandwich
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Sandwich cannot be deleted because other records still reference it") from e
    # 204 means "success, nothing to send back"
    return Response(status_code=status.HTTP_204_NO_CONTENT)