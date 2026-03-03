from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import MonthlyConfig, MonthlyException, AuditLog, User
from app.schemas.schemas import (
    MonthlyConfigCreate, MonthlyConfigUpdate, MonthlyConfigResponse,
    ExceptionCreate, ExceptionResponse,
)

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("/{year}/{month}", response_model=MonthlyConfigResponse)
def get_config(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration found for {month}/{year}")

    resp = MonthlyConfigResponse.model_validate(config)
    resp.monthly_threshold = config.working_days * config.threshold_hours_per_day
    resp.monthly_expected = config.working_days * config.full_day_hours
    return resp


@router.post("", response_model=MonthlyConfigResponse)
def create_config(
    data: MonthlyConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == data.year,
        MonthlyConfig.month == data.month,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Configuration for {data.month}/{data.year} already exists")

    config = MonthlyConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)

    db.add(AuditLog(
        action="create",
        entity_type="monthly_config",
        entity_id=config.id,
        new_value=json.dumps(data.model_dump(), default=str),
        performed_by=current_user.email,
    ))
    db.commit()

    resp = MonthlyConfigResponse.model_validate(config)
    resp.monthly_threshold = config.working_days * config.threshold_hours_per_day
    resp.monthly_expected = config.working_days * config.full_day_hours
    return resp


@router.patch("/{year}/{month}", response_model=MonthlyConfigResponse)
def update_config(
    year: int,
    month: int,
    data: MonthlyConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration found for {month}/{year}")
    if config.status == "finalized":
        raise HTTPException(status_code=400, detail="Cannot modify finalized configuration")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)

    resp = MonthlyConfigResponse.model_validate(config)
    resp.monthly_threshold = config.working_days * config.threshold_hours_per_day
    resp.monthly_expected = config.working_days * config.full_day_hours
    return resp


# --- Exception Management ---

@router.get("/{year}/{month}/exceptions", response_model=list[ExceptionResponse])
def list_exceptions(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration found for {month}/{year}")
    return db.query(MonthlyException).filter(MonthlyException.config_id == config.id).all()


@router.post("/{year}/{month}/exceptions", response_model=ExceptionResponse)
def add_exception(
    year: int,
    month: int,
    data: ExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration found for {month}/{year}")
    if config.status == "finalized":
        raise HTTPException(status_code=400, detail="Cannot modify finalized configuration")

    exception = MonthlyException(
        config_id=config.id,
        employee_id=data.employee_id,
        exception_type=data.exception_type,
        value=data.value,
        reason=data.reason,
        created_by=current_user.email,
    )
    db.add(exception)

    db.add(AuditLog(
        action="add_exception",
        entity_type="monthly_exception",
        entity_id=data.employee_id,
        new_value=json.dumps(data.model_dump(), default=str),
        performed_by=current_user.email,
        reason=data.reason,
    ))
    db.commit()
    db.refresh(exception)
    return exception


@router.delete("/{year}/{month}/exceptions/{exception_id}")
def remove_exception(
    year: int,
    month: int,
    exception_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exception = db.query(MonthlyException).filter(MonthlyException.id == exception_id).first()
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")

    db.add(AuditLog(
        action="remove_exception",
        entity_type="monthly_exception",
        entity_id=exception.employee_id,
        old_value=json.dumps({
            "exception_type": exception.exception_type.value,
            "value": exception.value,
        }),
        performed_by=current_user.email,
    ))
    db.delete(exception)
    db.commit()
    return {"message": "Exception removed"}
