"""
Payroll Calculation Engine — ported directly from the tested prototype.

Implements the dual-threshold formula:
  - DEDUCT: total_billable < threshold (shortfall from FULL 9-hour day)
  - OK: threshold <= total_billable <= expected (no adjustment)
  - ADDITION: total_billable > expected (overtime from 9-hour day)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PayrollInput:
    employee_name: str
    salary: float
    currency: str
    reimbursement: float
    actual_hours: float
    days_worked: int
    leaves_considered: float
    manual_hours: float
    manual_leave_days: float
    exception_type: Optional[str]  # "fixed_salary", "full_month_absent", or None
    insightful_match: str
    working_days: int
    full_day_hours: float = 9.0
    threshold_hours_per_day: float = 8.25


@dataclass
class PayrollResult:
    employee_name: str
    salary: float
    currency: str
    actual_hours: float
    days_worked: int
    leaves_considered: float
    leave_hours: float
    manual_hours: float
    manual_leave_days: float
    manual_leave_hours: float
    total_billable_hours: float
    monthly_expected: float
    monthly_threshold: float
    hourly_rate: float
    status: str  # "DEDUCT", "OK", "ADDITION", "FIXED", "FULL_ABSENT"
    deduction: float
    addition: float
    final_salary: float
    reimbursement: float
    total_pay: float
    insightful_match: str
    notes: str


def calculate_employee_payroll(inp: PayrollInput) -> PayrollResult:
    """
    Calculate payroll for a single employee using the dual-threshold formula.

    This is a faithful port of the logic from calculate_salaries.py that was
    tested against real February 2026 data.
    """
    monthly_expected = inp.working_days * inp.full_day_hours
    monthly_threshold = inp.working_days * inp.threshold_hours_per_day

    # --- Handle exceptions first ---
    if inp.exception_type == "fixed_salary":
        return PayrollResult(
            employee_name=inp.employee_name,
            salary=inp.salary,
            currency=inp.currency,
            actual_hours=0,
            days_worked=0,
            leaves_considered=0,
            leave_hours=0,
            manual_hours=0,
            manual_leave_days=0,
            manual_leave_hours=0,
            total_billable_hours=0,
            monthly_expected=monthly_expected,
            monthly_threshold=monthly_threshold,
            hourly_rate=0,
            status="FIXED",
            deduction=0,
            addition=0,
            final_salary=inp.salary,
            reimbursement=inp.reimbursement,
            total_pay=round(inp.salary + inp.reimbursement, 2),
            insightful_match="N/A (Exception)",
            notes="Fixed salary — no hour tracking",
        )

    if inp.exception_type == "full_month_absent":
        hourly_rate = inp.salary / monthly_expected if monthly_expected > 0 else 0
        return PayrollResult(
            employee_name=inp.employee_name,
            salary=inp.salary,
            currency=inp.currency,
            actual_hours=0,
            days_worked=0,
            leaves_considered=0,
            leave_hours=0,
            manual_hours=0,
            manual_leave_days=0,
            manual_leave_hours=0,
            total_billable_hours=0,
            monthly_expected=monthly_expected,
            monthly_threshold=monthly_threshold,
            hourly_rate=round(hourly_rate, 4),
            status="FULL_ABSENT",
            deduction=inp.salary,
            addition=0,
            final_salary=0,
            reimbursement=inp.reimbursement,
            total_pay=round(inp.reimbursement, 2),
            insightful_match="N/A (Full absent)",
            notes="Full month absent — full deduction",
        )

    # --- Standard calculation ---
    leave_hours = inp.leaves_considered * inp.full_day_hours
    manual_leave_hours = inp.manual_leave_days * inp.full_day_hours
    total_billable_hours = inp.actual_hours + leave_hours + manual_leave_hours + inp.manual_hours
    hourly_rate = inp.salary / monthly_expected if monthly_expected > 0 else 0

    deduction = 0.0
    addition = 0.0
    status = ""
    notes = ""

    if total_billable_hours < monthly_threshold:
        # DEDUCT: shortfall measured from FULL 9-hour day, NOT from threshold
        shortfall = monthly_expected - total_billable_hours
        deduction = shortfall * hourly_rate
        status = "DEDUCT"
        notes = f"Short by {shortfall:.2f} hrs from {monthly_expected}"
    elif total_billable_hours > monthly_expected:
        # ADDITION: overtime above full 9-hour day
        excess = total_billable_hours - monthly_expected
        addition = excess * hourly_rate
        status = "ADDITION"
        notes = f"Overtime {excess:.2f} hrs above {monthly_expected}"
    else:
        # OK: within the grace zone (threshold <= billable <= expected)
        status = "OK"
        notes = "Within threshold, no adjustment"

    final_salary = inp.salary - deduction + addition
    total_pay = final_salary + inp.reimbursement

    return PayrollResult(
        employee_name=inp.employee_name,
        salary=inp.salary,
        currency=inp.currency,
        actual_hours=round(inp.actual_hours, 2),
        days_worked=inp.days_worked,
        leaves_considered=inp.leaves_considered,
        leave_hours=round(leave_hours, 2),
        manual_hours=round(inp.manual_hours, 2),
        manual_leave_days=inp.manual_leave_days,
        manual_leave_hours=round(manual_leave_hours, 2),
        total_billable_hours=round(total_billable_hours, 2),
        monthly_expected=monthly_expected,
        monthly_threshold=monthly_threshold,
        hourly_rate=round(hourly_rate, 4),
        status=status,
        deduction=round(deduction, 2),
        addition=round(addition, 2),
        final_salary=round(final_salary, 2),
        reimbursement=inp.reimbursement,
        total_pay=round(total_pay, 2),
        insightful_match=inp.insightful_match,
        notes=notes,
    )


def match_employee_name(salary_name: str, insightful_hours: dict, name_mappings: dict) -> Optional[str]:
    """
    Match an employee name from the Salary Sheet to the Insightful system.

    Priority: explicit mapping > exact match > first name > last name > partial.
    Ported directly from the prototype's match_employee_name function.
    """
    # 1. Check explicit name mappings
    if salary_name in name_mappings:
        mapped = name_mappings[salary_name].lower()
        if mapped in insightful_hours:
            return mapped

    # 2. Direct match (case-insensitive)
    if salary_name.lower() in insightful_hours:
        return salary_name.lower()

    # 3. First name match
    first_name = salary_name.split()[0].lower()
    matches = [k for k in insightful_hours.keys() if k.startswith(first_name)]
    if len(matches) == 1:
        return matches[0]

    # 4. Last name match
    parts = salary_name.split()
    if len(parts) > 1:
        last_name = parts[-1].lower()
        matches = [k for k in insightful_hours.keys() if last_name in k]
        if len(matches) == 1:
            return matches[0]

    # 5. Partial match
    for key in insightful_hours.keys():
        if first_name in key or key in salary_name.lower():
            return key

    return None


def match_leave_name(salary_name: str, leave_data: dict) -> Optional[dict]:
    """
    Match an employee name from the Salary Sheet to the Leave data.
    Handles Unicode characters (e.g., word joiner \\u2060).
    """
    clean = salary_name.replace('\u2060', '').strip()

    # Exact match (case-insensitive)
    for leave_name, linfo in leave_data.items():
        if leave_name.lower() == clean.lower():
            return linfo

    # First name match
    first = clean.split()[0].lower()
    for leave_name, linfo in leave_data.items():
        if leave_name.split()[0].lower() == first:
            return linfo

    return None
