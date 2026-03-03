from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from enum import Enum


# --- Enums ---

class CurrencyType(str, Enum):
    INR = "INR"
    GBP = "GBP"
    AED = "AED"
    USD = "USD"


class ExceptionType(str, Enum):
    FIXED_SALARY = "fixed_salary"
    FULL_MONTH_ABSENT = "full_month_absent"
    NAME_MAPPING = "name_mapping"
    MANUAL_HOURS = "manual_hours"
    MANUAL_LEAVES = "manual_leaves"


class UserRole(str, Enum):
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    VIEWER = "viewer"


class LeaveRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# --- Employee Schemas ---

class EmployeeCreate(BaseModel):
    name: str
    email: Optional[str] = None
    salary: float
    currency: CurrencyType = CurrencyType.INR
    start_date: Optional[date] = None
    exception_type: Optional[ExceptionType] = None
    insightful_name: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    salary: Optional[float] = None
    currency: Optional[CurrencyType] = None
    start_date: Optional[date] = None
    exception_type: Optional[ExceptionType] = None
    insightful_name: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    salary: float
    currency: CurrencyType
    start_date: Optional[date]
    exception_type: Optional[ExceptionType]
    insightful_name: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Monthly Config Schemas ---

class MonthlyConfigCreate(BaseModel):
    month: int  # 1-12
    year: int
    working_days: int
    full_day_hours: float = 9.0
    threshold_hours_per_day: float = 8.25


class MonthlyConfigUpdate(BaseModel):
    working_days: Optional[int] = None
    full_day_hours: Optional[float] = None
    threshold_hours_per_day: Optional[float] = None


class MonthlyConfigResponse(BaseModel):
    id: int
    month: int
    year: int
    working_days: int
    full_day_hours: float
    threshold_hours_per_day: float
    status: str
    finalized_by: Optional[str]
    finalized_at: Optional[datetime]
    monthly_threshold: float = 0
    monthly_expected: float = 0

    model_config = {"from_attributes": True}


# --- Exception Schemas ---

class ExceptionCreate(BaseModel):
    employee_id: int
    exception_type: ExceptionType
    value: Optional[str] = None
    reason: Optional[str] = None


class ExceptionResponse(BaseModel):
    id: int
    config_id: int
    employee_id: int
    exception_type: ExceptionType
    value: Optional[str]
    reason: Optional[str]
    created_by: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Compensation Schemas ---

class CompensationCreate(BaseModel):
    employee_id: int
    month: int
    year: int
    hours: float
    reason: str


class CompensationResponse(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    hours: float
    reason: str
    submitted_by: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Leave Schemas ---

class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: Optional[str] = None
    start_date: date
    end_date: date
    num_days: float
    reason: Optional[str] = None


class LeaveRequestUpdate(BaseModel):
    status: LeaveRequestStatus
    approved_by: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: Optional[str]
    start_date: date
    end_date: date
    num_days: float
    status: LeaveRequestStatus
    reason: Optional[str]
    approved_by: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    year: int
    accrued_days: float
    used_days: float
    remaining_days: float
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Payroll Schemas ---

class PayrollResultResponse(BaseModel):
    id: int
    config_id: int
    employee_id: int
    employee_name: str
    salary: float
    currency: CurrencyType
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
    status: str
    deduction: float
    addition: float
    final_salary: float
    reimbursement: float
    total_pay: float
    insightful_match: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class PayrollSummary(BaseModel):
    total_employees: int
    deductions_count: int
    additions_count: int
    ok_count: int
    fixed_count: int
    absent_count: int
    total_deductions: float
    total_additions: float
    total_gross_salary: float
    total_net_salary: float


class PayrollRunResponse(BaseModel):
    summary: PayrollSummary
    results: list[PayrollResultResponse]
    config: MonthlyConfigResponse


# --- User / Auth Schemas ---

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- Audit Log ---

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: Optional[str]
    reason: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
