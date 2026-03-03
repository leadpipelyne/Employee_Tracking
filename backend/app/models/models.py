from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text,
    ForeignKey, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


# --- Enums ---

class CurrencyType(str, enum.Enum):
    INR = "INR"
    GBP = "GBP"
    AED = "AED"
    USD = "USD"


class ExceptionType(str, enum.Enum):
    FIXED_SALARY = "fixed_salary"
    FULL_MONTH_ABSENT = "full_month_absent"
    NAME_MAPPING = "name_mapping"
    MANUAL_HOURS = "manual_hours"
    MANUAL_LEAVES = "manual_leaves"


class PayrollStatus(str, enum.Enum):
    DEDUCT = "DEDUCT"
    OK = "OK"
    ADDITION = "ADDITION"
    FIXED = "FIXED"
    FULL_ABSENT = "FULL_ABSENT"


class MonthStatus(str, enum.Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    FINALIZED = "finalized"


class LeaveRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    VIEWER = "viewer"


# --- Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    salary = Column(Float, nullable=False)
    currency = Column(SQLEnum(CurrencyType), default=CurrencyType.INR, nullable=False)
    start_date = Column(Date, nullable=True)
    exception_type = Column(SQLEnum(ExceptionType), nullable=True)
    insightful_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    daily_hours = relationship("DailyHours", back_populates="employee")
    leave_balance = relationship("LeaveBalance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    compensation_logs = relationship("CompensationLog", back_populates="employee")
    payroll_results = relationship("PayrollResult", back_populates="employee")


class MonthlyConfig(Base):
    __tablename__ = "monthly_configs"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    working_days = Column(Integer, nullable=False)
    full_day_hours = Column(Float, default=9.0)
    threshold_hours_per_day = Column(Float, default=8.25)
    insightful_token = Column(Text, nullable=True)
    status = Column(SQLEnum(MonthStatus), default=MonthStatus.DRAFT)
    finalized_by = Column(String(255), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("month", "year", name="uq_month_year"),
    )

    # Relationships
    exceptions = relationship("MonthlyException", back_populates="config")
    payroll_results = relationship("PayrollResult", back_populates="config")


class MonthlyException(Base):
    __tablename__ = "monthly_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("monthly_configs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    exception_type = Column(SQLEnum(ExceptionType), nullable=False)
    value = Column(String(255), nullable=True)  # For name mappings or hour/leave amounts
    reason = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("MonthlyConfig", back_populates="exceptions")
    employee = relationship("Employee")


class DailyHours(Base):
    __tablename__ = "daily_hours"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    hours_worked = Column(Float, default=0.0)
    shift_count = Column(Integer, default=0)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_employee_date"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="daily_hours")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    year = Column(Integer, nullable=False)
    accrued_days = Column(Float, default=0.0)
    used_days = Column(Float, default=0.0)
    remaining_days = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("employee_id", "year", name="uq_employee_year_balance"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="leave_balance")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(100), nullable=True)  # Sick, Casual, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    num_days = Column(Float, nullable=False)
    status = Column(SQLEnum(LeaveRequestStatus), default=LeaveRequestStatus.PENDING)
    reason = Column(Text, nullable=True)
    approved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="leave_requests")


class CompensationLog(Base):
    __tablename__ = "compensation_logs"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    hours = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    submitted_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="compensation_logs")


class PayrollResult(Base):
    __tablename__ = "payroll_results"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("monthly_configs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_name = Column(String(255), nullable=False)
    salary = Column(Float, nullable=False)
    currency = Column(SQLEnum(CurrencyType), default=CurrencyType.INR)
    actual_hours = Column(Float, default=0.0)
    days_worked = Column(Integer, default=0)
    leaves_considered = Column(Float, default=0.0)
    leave_hours = Column(Float, default=0.0)
    manual_hours = Column(Float, default=0.0)
    manual_leave_days = Column(Float, default=0.0)
    manual_leave_hours = Column(Float, default=0.0)
    total_billable_hours = Column(Float, default=0.0)
    monthly_expected = Column(Float, default=0.0)
    monthly_threshold = Column(Float, default=0.0)
    hourly_rate = Column(Float, default=0.0)
    status = Column(SQLEnum(PayrollStatus), nullable=False)
    deduction = Column(Float, default=0.0)
    addition = Column(Float, default=0.0)
    final_salary = Column(Float, default=0.0)
    reimbursement = Column(Float, default=0.0)
    total_pay = Column(Float, default=0.0)
    insightful_match = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("config_id", "employee_id", name="uq_config_employee"),
    )

    # Relationships
    config = relationship("MonthlyConfig", back_populates="payroll_results")
    employee = relationship("Employee", back_populates="payroll_results")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    performed_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    generated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
