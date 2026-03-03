from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import json
import csv
import io

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    Employee, AuditLog, User, PayrollResult, MonthlyException,
    CompensationLog, LeaveBalance, LeaveRequest
)
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


@router.post("/bulk-upload")
def bulk_upload_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk upload employees via CSV or JSON file.

    CSV format: name,email,salary,currency,start_date,exception_type,insightful_name
    JSON format: [{"name": "...", "salary": ..., "currency": "INR", ...}, ...]
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = file.file.read().decode("utf-8")
    employees_data = []

    if file.filename.endswith(".json"):
        try:
            employees_data = json.loads(content)
            if not isinstance(employees_data, list):
                raise HTTPException(status_code=400, detail="JSON must be an array of employee objects")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    elif file.filename.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                emp_data = {}
                for key, value in row.items():
                    key = key.strip().lower().replace(" ", "_")
                    if value:
                        value = value.strip()
                    emp_data[key] = value
                employees_data.append(emp_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="File must be .csv or .json")

    if not employees_data:
        raise HTTPException(status_code=400, detail="File contains no employee data")

    valid_currencies = {"INR", "GBP", "AED", "USD"}
    valid_exceptions = {"fixed_salary", "full_month_absent", "name_mapping", "manual_hours", "manual_leaves", "", None}

    created = []
    errors = []

    for i, emp_data in enumerate(employees_data):
        row_num = i + 1
        try:
            name = emp_data.get("name", "").strip()
            if not name:
                errors.append(f"Row {row_num}: Name is required")
                continue

            salary_str = str(emp_data.get("salary", "0")).strip()
            try:
                salary = float(salary_str)
            except (ValueError, TypeError):
                errors.append(f"Row {row_num} ({name}): Invalid salary '{salary_str}'")
                continue

            if salary <= 0:
                errors.append(f"Row {row_num} ({name}): Salary must be positive")
                continue

            currency = str(emp_data.get("currency", "INR")).strip().upper()
            if currency not in valid_currencies:
                errors.append(f"Row {row_num} ({name}): Invalid currency '{currency}'. Must be INR, GBP, AED, or USD")
                continue

            exception_type = emp_data.get("exception_type", "")
            if exception_type:
                exception_type = exception_type.strip().lower()
            if exception_type and exception_type not in valid_exceptions:
                errors.append(f"Row {row_num} ({name}): Invalid exception type '{exception_type}'")
                continue

            start_date = emp_data.get("start_date")
            if start_date and isinstance(start_date, str):
                start_date = start_date.strip()
                if not start_date:
                    start_date = None

            emp = Employee(
                name=name,
                email=emp_data.get("email", "").strip() or None,
                salary=salary,
                currency=currency,
                start_date=start_date if start_date else None,
                exception_type=exception_type if exception_type else None,
                insightful_name=emp_data.get("insightful_name", "").strip() or None,
            )
            db.add(emp)
            db.flush()
            created.append({"id": emp.id, "name": emp.name})

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    if created:
        db.add(AuditLog(
            action="bulk_upload",
            entity_type="employee",
            new_value=json.dumps({
                "count": len(created),
                "names": [e["name"] for e in created],
                "file": file.filename,
            }),
            performed_by=current_user.email,
        ))
        db.commit()

    return {
        "created": len(created),
        "errors": len(errors),
        "created_employees": created,
        "error_details": errors,
    }


@router.get("/{employee_id}/profile")
def get_employee_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed employee profile with payroll history, exceptions, and leave info."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Payroll history
    payroll_results = (
        db.query(PayrollResult)
        .filter(PayrollResult.employee_id == employee_id)
        .order_by(PayrollResult.created_at.desc())
        .all()
    )

    # Monthly exceptions
    exceptions = (
        db.query(MonthlyException)
        .filter(MonthlyException.employee_id == employee_id)
        .order_by(MonthlyException.created_at.desc())
        .all()
    )

    # Compensation logs (manual hours)
    compensation_logs = (
        db.query(CompensationLog)
        .filter(CompensationLog.employee_id == employee_id)
        .order_by(CompensationLog.created_at.desc())
        .all()
    )

    # Leave balances
    leave_balances = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.employee_id == employee_id)
        .all()
    )

    # Leave requests
    leave_requests = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )

    return {
        "employee": {
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "salary": emp.salary,
            "currency": emp.currency.value if emp.currency else "INR",
            "start_date": str(emp.start_date) if emp.start_date else None,
            "exception_type": emp.exception_type.value if emp.exception_type else None,
            "insightful_name": emp.insightful_name,
            "is_active": emp.is_active,
            "created_at": str(emp.created_at) if emp.created_at else None,
            "updated_at": str(emp.updated_at) if emp.updated_at else None,
        },
        "payroll_history": [
            {
                "id": pr.id,
                "month": pr.config.month if pr.config else None,
                "year": pr.config.year if pr.config else None,
                "actual_hours": pr.actual_hours,
                "total_billable_hours": pr.total_billable_hours,
                "status": pr.status.value if pr.status else None,
                "deduction": pr.deduction,
                "addition": pr.addition,
                "final_salary": pr.final_salary,
                "total_pay": pr.total_pay,
                "notes": pr.notes,
                "created_at": str(pr.created_at) if pr.created_at else None,
            }
            for pr in payroll_results
        ],
        "exceptions": [
            {
                "id": ex.id,
                "config_id": ex.config_id,
                "exception_type": ex.exception_type.value if ex.exception_type else None,
                "value": ex.value,
                "reason": ex.reason,
                "created_by": ex.created_by,
                "created_at": str(ex.created_at) if ex.created_at else None,
            }
            for ex in exceptions
        ],
        "compensation_logs": [
            {
                "id": cl.id,
                "month": cl.month,
                "year": cl.year,
                "hours": cl.hours,
                "reason": cl.reason,
                "submitted_by": cl.submitted_by,
                "created_at": str(cl.created_at) if cl.created_at else None,
            }
            for cl in compensation_logs
        ],
        "leave_balances": [
            {
                "id": lb.id,
                "year": lb.year,
                "accrued_days": lb.accrued_days,
                "used_days": lb.used_days,
                "remaining_days": lb.remaining_days,
            }
            for lb in leave_balances
        ],
        "leave_requests": [
            {
                "id": lr.id,
                "leave_type": lr.leave_type,
                "start_date": str(lr.start_date) if lr.start_date else None,
                "end_date": str(lr.end_date) if lr.end_date else None,
                "num_days": lr.num_days,
                "status": lr.status.value if lr.status else None,
                "reason": lr.reason,
                "approved_by": lr.approved_by,
                "created_at": str(lr.created_at) if lr.created_at else None,
            }
            for lr in leave_requests
        ],
    }
