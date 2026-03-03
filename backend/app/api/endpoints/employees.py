from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import Employee, AuditLog, User
from app.schemas.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeResponse])
def list_employees(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Employee)
    if active_only:
        query = query.filter(Employee.is_active == True)
    return query.order_by(Employee.name).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("", response_model=EmployeeResponse)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp = Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)

    db.add(AuditLog(
        action="create",
        entity_type="employee",
        entity_id=emp.id,
        new_value=json.dumps(data.model_dump(), default=str),
        performed_by=current_user.email,
    ))
    db.commit()
    return emp


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    old_values = {}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        old_values[key] = getattr(emp, key)
        setattr(emp, key, value)

    db.add(AuditLog(
        action="update",
        entity_type="employee",
        entity_id=emp.id,
        old_value=json.dumps(old_values, default=str),
        new_value=json.dumps(update_data, default=str),
        performed_by=current_user.email,
    ))
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{employee_id}")
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.is_active = False
    db.add(AuditLog(
        action="deactivate",
        entity_type="employee",
        entity_id=emp.id,
        old_value=json.dumps({"is_active": True}),
        new_value=json.dumps({"is_active": False}),
        performed_by=current_user.email,
    ))
    db.commit()
    return {"message": f"Employee {emp.name} deactivated"}
