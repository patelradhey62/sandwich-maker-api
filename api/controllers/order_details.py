from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from ..models import models


def create(db: Session, order_detail):
    # Create a new OrderDetail object with the data the client sent
    db_order_detail = models.OrderDetail(
        order_id=order_detail.order_id,
        sandwich_id=order_detail.sandwich_id,
        amount=order_detail.amount
    )
    try:
        # Add it to the session and save it to the database
        db.add(db_order_detail)
        db.commit()
    except IntegrityError as e:
        # Undo the failed save, then tell the client what went wrong
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Order detail could not be created: order_id and sandwich_id must reference existing records") from e
    # Reload the object so it includes the new id
    db.refresh(db_order_detail)
    return db_order_detail


def read_all(db: Session):
    # Get every row in the order_details table
    return db.query(models.OrderDetail).all()


def read_one(db: Session, order_detail_id):
    # Get the one row whose id matches (or None if there isn't one)
    return db.query(models.OrderDetail).filter(models.OrderDetail.id == order_detail_id).first()


def update(db: Session, order_detail_id, order_detail):
    # Find the row to update
    db_order_detail = db.query(models.OrderDetail).filter(models.OrderDetail.id == order_detail_id)
    # Only include the fields the client actually sent
    update_data = order_detail.model_dump(exclude_unset=True)
    if update_data:
        try:
            db_order_detail.update(update_data, synchronize_session=False)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Order detail could not be updated: order_id and sandwich_id must reference existing records") from e
    # Return the updated row
    return db_order_detail.first()


def delete(db: Session, order_detail_id):
    # Find the row to delete
    db_order_detail = db.query(models.OrderDetail).filter(models.OrderDetail.id == order_detail_id)
    try:
        db_order_detail.delete(synchronize_session=False)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Order detail cannot be deleted because other records still reference it") from e
    # 204 means "success, nothing to send back"
    return Response(status_code=status.HTTP_204_NO_CONTENT)