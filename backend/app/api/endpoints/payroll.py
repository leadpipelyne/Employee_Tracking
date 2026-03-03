from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    MonthlyConfig, MonthlyException, Employee, PayrollResult as PayrollResultModel,
    CompensationLog, LeaveRequest, AuditLog, User, Report,
)
from app.schemas.schemas import (
    PayrollResultResponse, PayrollRunResponse, PayrollSummary,
    CompensationCreate, CompensationResponse,
)
from app.services.payroll_engine import PayrollInput, calculate_employee_payroll, match_employee_name, match_leave_name
from app.services.insightful_service import get_monthly_hours_summary

router = APIRouter(prefix="/api/payroll", tags=["Payroll"])


@router.post("/calculate/{year}/{month}", response_model=PayrollRunResponse)
def run_payroll_calculation(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the payroll calculation for a given month."""
    # Get config
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration for {month}/{year}. Create one first.")
    if config.status == "finalized":
        raise HTTPException(status_code=400, detail="This month is already finalized. Unlock to recalculate.")

    # Get all active employees
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    if not employees:
        raise HTTPException(status_code=400, detail="No active employees found")

    # Get exceptions for this month
    exceptions = db.query(MonthlyException).filter(MonthlyException.config_id == config.id).all()
    exception_map = {}
    name_mappings = {}
    manual_hours_map = {}
    manual_leaves_map = {}
    for exc in exceptions:
        if exc.exception_type.value == "fixed_salary":
            exception_map[exc.employee_id] = "fixed_salary"
        elif exc.exception_type.value == "full_month_absent":
            exception_map[exc.employee_id] = "full_month_absent"
        elif exc.exception_type.value == "name_mapping":
            emp = db.query(Employee).filter(Employee.id == exc.employee_id).first()
            if emp and exc.value:
                name_mappings[emp.name] = exc.value
        elif exc.exception_type.value == "manual_hours":
            manual_hours_map[exc.employee_id] = float(exc.value) if exc.value else 0
        elif exc.exception_type.value == "manual_leaves":
            manual_leaves_map[exc.employee_id] = float(exc.value) if exc.value else 0

    # Also check compensation logs for this month
    comp_logs = db.query(CompensationLog).filter(
        CompensationLog.month == month,
        CompensationLog.year == year,
    ).all()
    for log in comp_logs:
        manual_hours_map[log.employee_id] = manual_hours_map.get(log.employee_id, 0) + log.hours

    # Get hours from database
    insightful_hours = get_monthly_hours_summary(db, year, month)

    # Get leave data from approved leave requests for this month
    from calendar import monthrange
    _, num_days = monthrange(year, month)
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, num_days).date()

    leave_requests = db.query(LeaveRequest).filter(
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= month_end,
        LeaveRequest.end_date >= month_start,
    ).all()

    leave_data = {}
    for lr in leave_requests:
        emp = db.query(Employee).filter(Employee.id == lr.employee_id).first()
        if emp:
            key = emp.name
            if key not in leave_data:
                leave_data[key] = {"name": key, "leaves_considered": 0, "status": "Approved"}
            leave_data[key]["leaves_considered"] += lr.num_days

    # Clear previous results for this config
    db.query(PayrollResultModel).filter(PayrollResultModel.config_id == config.id).delete()

    # Calculate for each employee
    results = []
    for emp in employees:
        # Determine exception type — monthly override takes priority, then employee default
        exc_type = exception_map.get(emp.id)
        if not exc_type and emp.exception_type:
            exc_type = emp.exception_type.value if hasattr(emp.exception_type, 'value') else emp.exception_type

        # Match to Insightful hours
        insightful_key = match_employee_name(emp.name, insightful_hours, name_mappings)
        if insightful_key and insightful_key in insightful_hours:
            actual_hours = insightful_hours[insightful_key]["total_hours"]
            days_worked = insightful_hours[insightful_key]["days_worked"]
            match_label = f"Yes ({insightful_hours[insightful_key]['name']})"
        else:
            actual_hours = 0
            days_worked = 0
            match_label = "No"

        # Match to leave data
        leave_info = match_leave_name(emp.name, leave_data)
        leaves_considered = leave_info["leaves_considered"] if leave_info else 0

        # Get manual adjustments
        manual_hours = manual_hours_map.get(emp.id, 0)
        manual_leave_days = manual_leaves_map.get(emp.id, 0)

        # Run the calculation
        calc_input = PayrollInput(
            employee_name=emp.name,
            salary=emp.salary,
            currency=emp.currency.value if emp.currency else "INR",
            reimbursement=0,  # Will be set from uploaded salary sheet
            actual_hours=actual_hours,
            days_worked=days_worked,
            leaves_considered=leaves_considered,
            manual_hours=manual_hours,
            manual_leave_days=manual_leave_days,
            exception_type=exc_type,
            insightful_match=match_label,
            working_days=config.working_days,
            full_day_hours=config.full_day_hours,
            threshold_hours_per_day=config.threshold_hours_per_day,
        )

        result = calculate_employee_payroll(calc_input)

        # Store in database
        db_result = PayrollResultModel(
            config_id=config.id,
            employee_id=emp.id,
            employee_name=result.employee_name,
            salary=result.salary,
            currency=emp.currency,
            actual_hours=result.actual_hours,
            days_worked=result.days_worked,
            leaves_considered=result.leaves_considered,
            leave_hours=result.leave_hours,
            manual_hours=result.manual_hours,
            manual_leave_days=result.manual_leave_days,
            manual_leave_hours=result.manual_leave_hours,
            total_billable_hours=result.total_billable_hours,
            monthly_expected=result.monthly_expected,
            monthly_threshold=result.monthly_threshold,
            hourly_rate=result.hourly_rate,
            status=result.status,
            deduction=result.deduction,
            addition=result.addition,
            final_salary=result.final_salary,
            reimbursement=result.reimbursement,
            total_pay=result.total_pay,
            insightful_match=result.insightful_match,
            notes=result.notes,
        )
        db.add(db_result)
        results.append(db_result)

    # Update config status
    config.status = "calculated"
    db.add(AuditLog(
        action="calculate_payroll",
        entity_type="monthly_config",
        entity_id=config.id,
        new_value=json.dumps({"month": month, "year": year, "employees": len(results)}),
        performed_by=current_user.email,
    ))
    db.commit()

    # Refresh all results to get IDs
    for r in results:
        db.refresh(r)

    # Build summary
    status_counts = {"DEDUCT": 0, "OK": 0, "ADDITION": 0, "FIXED": 0, "FULL_ABSENT": 0}
    total_ded = total_add = total_gross = total_net = 0.0
    for r in results:
        status_counts[r.status.value if hasattr(r.status, 'value') else r.status] = \
            status_counts.get(r.status.value if hasattr(r.status, 'value') else r.status, 0) + 1
        total_ded += r.deduction
        total_add += r.addition
        total_gross += r.salary
        total_net += r.final_salary

    from app.schemas.schemas import MonthlyConfigResponse
    config_resp = MonthlyConfigResponse.model_validate(config)
    config_resp.monthly_threshold = config.working_days * config.threshold_hours_per_day
    config_resp.monthly_expected = config.working_days * config.full_day_hours

    return PayrollRunResponse(
        summary=PayrollSummary(
            total_employees=len(results),
            deductions_count=status_counts.get("DEDUCT", 0),
            additions_count=status_counts.get("ADDITION", 0),
            ok_count=status_counts.get("OK", 0),
            fixed_count=status_counts.get("FIXED", 0),
            absent_count=status_counts.get("FULL_ABSENT", 0),
            total_deductions=round(total_ded, 2),
            total_additions=round(total_add, 2),
            total_gross_salary=round(total_gross, 2),
            total_net_salary=round(total_net, 2),
        ),
        results=[PayrollResultResponse.model_validate(r) for r in results],
        config=config_resp,
    )


@router.get("/results/{year}/{month}", response_model=PayrollRunResponse)
def get_payroll_results(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get previously calculated payroll results."""
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration for {month}/{year}")

    results = db.query(PayrollResultModel).filter(
        PayrollResultModel.config_id == config.id
    ).all()
    if not results:
        raise HTTPException(status_code=404, detail="No payroll results found. Run calculation first.")

    # Build summary
    status_counts = {"DEDUCT": 0, "OK": 0, "ADDITION": 0, "FIXED": 0, "FULL_ABSENT": 0}
    total_ded = total_add = total_gross = total_net = 0.0
    for r in results:
        st = r.status.value if hasattr(r.status, 'value') else r.status
        status_counts[st] = status_counts.get(st, 0) + 1
        total_ded += r.deduction
        total_add += r.addition
        total_gross += r.salary
        total_net += r.final_salary

    from app.schemas.schemas import MonthlyConfigResponse
    config_resp = MonthlyConfigResponse.model_validate(config)
    config_resp.monthly_threshold = config.working_days * config.threshold_hours_per_day
    config_resp.monthly_expected = config.working_days * config.full_day_hours

    return PayrollRunResponse(
        summary=PayrollSummary(
            total_employees=len(results),
            deductions_count=status_counts.get("DEDUCT", 0),
            additions_count=status_counts.get("ADDITION", 0),
            ok_count=status_counts.get("OK", 0),
            fixed_count=status_counts.get("FIXED", 0),
            absent_count=status_counts.get("FULL_ABSENT", 0),
            total_deductions=round(total_ded, 2),
            total_additions=round(total_add, 2),
            total_gross_salary=round(total_gross, 2),
            total_net_salary=round(total_net, 2),
        ),
        results=[PayrollResultResponse.model_validate(r) for r in results],
        config=config_resp,
    )


@router.post("/finalize/{year}/{month}")
def finalize_payroll(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lock the payroll results and mark as finalized."""
    config = db.query(MonthlyConfig).filter(
        MonthlyConfig.year == year,
        MonthlyConfig.month == month,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"No configuration for {month}/{year}")
    if config.status == "finalized":
        raise HTTPException(status_code=400, detail="Already finalized")
    if config.status != "calculated":
        raise HTTPException(status_code=400, detail="Run calculation first before finalizing")

    config.status = "finalized"
    config.finalized_by = current_user.email
    config.finalized_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        action="finalize_payroll",
        entity_type="monthly_config",
        entity_id=config.id,
        new_value=json.dumps({"finalized_by": current_user.email}),
        performed_by=current_user.email,
    ))
    db.commit()
    return {"message": f"Payroll for {month}/{year} finalized by {current_user.email}"}


# --- Compensation Logs ---

@router.post("/compensation", response_model=CompensationResponse)
def add_compensation(
    data: CompensationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add manual compensation hours for an employee."""
    emp = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    log = CompensationLog(
        employee_id=data.employee_id,
        month=data.month,
        year=data.year,
        hours=data.hours,
        reason=data.reason,
        submitted_by=current_user.email,
    )
    db.add(log)
    db.add(AuditLog(
        action="add_compensation",
        entity_type="compensation_log",
        entity_id=data.employee_id,
        new_value=json.dumps(data.model_dump(), default=str),
        performed_by=current_user.email,
        reason=data.reason,
    ))
    db.commit()
    db.refresh(log)
    return log


@router.get("/compensation/{employee_id}", response_model=list[CompensationResponse])
def get_compensation_history(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(CompensationLog).filter(
        CompensationLog.employee_id == employee_id
    ).order_by(CompensationLog.created_at.desc()).all()
