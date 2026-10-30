from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from ..models import models


def create(db: Session, recipe):
    # Create a new Recipe object with the data the client sent
    db_recipe = models.Recipe(
        sandwich_id=recipe.sandwich_id,
        resource_id=recipe.resource_id,
        amount=recipe.amount
    )
    try:
        # Add it to the session and save it to the database
        db.add(db_recipe)
        db.commit()
    except IntegrityError as e:
        # Undo the failed save, then tell the client what went wrong
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Recipe could not be created: sandwich_id and resource_id must reference existing records") from e
    # Reload the object so it includes the new id
    db.refresh(db_recipe)
    return db_recipe


def read_all(db: Session):
    # Get every row in the recipes table
    return db.query(models.Recipe).all()


def read_one(db: Session, recipe_id):
    # Get the one row whose id matches (or None if there isn't one)
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()


def update(db: Session, recipe_id, recipe):
    # Find the row to update
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id)
    # Only include the fields the client actually sent
    update_data = recipe.model_dump(exclude_unset=True)
    if update_data:
        try:
            db_recipe.update(update_data, synchronize_session=False)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Recipe could not be updated: sandwich_id and resource_id must reference existing records") from e
    # Return the updated row
    return db_recipe.first()


def delete(db: Session, recipe_id):
    # Find the row to delete
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id)
    try:
        db_recipe.delete(synchronize_session=False)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Recipe cannot be deleted because other records still reference it") from e
    # 204 means "success, nothing to send back"
    return Response(status_code=status.HTTP_204_NO_CONTENT)