"""
Insightful API Integration Service.

Ported from fetch_insightful_data.py — fetches hours data week-by-week
from the Insightful API and stores it in the database.
"""

import time
import httpx
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Employee, DailyHours


def date_to_ms(date_str: str) -> int:
    """Convert date string (YYYY-MM-DD) to unix timestamp in milliseconds (start of day UTC)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def date_to_ms_end(date_str: str) -> int:
    """Convert date string to unix timestamp in milliseconds (end of day UTC, 23:59:59.999)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000) + 86400000 - 1


def get_week_ranges(year: int, month: int) -> list[tuple[str, str]]:
    """Generate week-by-week date ranges for a given month."""
    from calendar import monthrange
    _, num_days = monthrange(year, month)

    start = datetime(year, month, 1)
    ranges = []

    current = start
    while current.month == month:
        week_end = current + timedelta(days=6)
        if week_end.month != month or week_end.day > num_days:
            week_end = datetime(year, month, num_days)
        ranges.append((current.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        current = week_end + timedelta(days=1)
        if current.month != month:
            break

    return ranges


async def fetch_employees_from_insightful(token: str) -> list[dict]:
    """Fetch the employee list from Insightful API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{settings.INSIGHTFUL_API_BASE_URL}/employee", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def fetch_shifts_for_week(token: str, start_date: str, end_date: str) -> list[dict]:
    """Fetch all shifts for a given date range from the Insightful API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    start_ms = date_to_ms(start_date)
    end_ms = date_to_ms_end(end_date)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{settings.INSIGHTFUL_API_BASE_URL}/analytics/shift",
            params={"start": start_ms, "end": end_ms},
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def sync_hours_for_month(
    db: Session,
    year: int,
    month: int,
    token: str,
) -> dict:
    """
    Sync hours from Insightful for a given month.

    Fetches data week-by-week (as required by the API) and stores daily hours
    in the database. Returns a summary of hours per employee.
    """
    # Get employee list from Insightful
    employees = await fetch_employees_from_insightful(token)
    emp_map = {}
    for emp in employees:
        emp_map[emp["id"]] = {
            "id": emp["id"],
            "name": emp["name"],
            "email": emp.get("email", ""),
        }

    # Fetch shifts week by week
    week_ranges = get_week_ranges(year, month)
    all_shifts = []
    for start_date, end_date in week_ranges:
        shifts = await fetch_shifts_for_week(token, start_date, end_date)
        all_shifts.extend(shifts)
        await _async_sleep(1)  # Rate limiting — 1 second between requests

    # Aggregate by employee and day
    emp_daily = defaultdict(lambda: defaultdict(float))
    emp_shift_count = defaultdict(int)

    for shift in all_shifts:
        emp_id = shift["employeeId"]
        duration_hrs = shift["duration"] / (1000 * 3600)  # ms to hours
        emp_shift_count[emp_id] += 1

        start_ts = shift.get("startTranslated", shift["start"])
        day_str = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        emp_daily[emp_id][day_str] += duration_hrs

    # Store in database
    results = {}
    for emp_id, daily_hours in emp_daily.items():
        emp_info = emp_map.get(emp_id, {"name": f"Unknown ({emp_id})", "email": ""})
        total_hours = sum(daily_hours.values())

        # Find or match the DB employee
        db_employee = _find_db_employee(db, emp_info["name"])

        for day_str, hours in daily_hours.items():
            day_date = datetime.strptime(day_str, "%Y-%m-%d").date()
            # Upsert daily hours
            existing = db.query(DailyHours).filter(
                DailyHours.employee_id == db_employee.id if db_employee else -1,
                DailyHours.date == day_date,
            ).first() if db_employee else None

            if existing:
                existing.hours_worked = round(hours, 4)
                existing.shift_count = 1
            elif db_employee:
                db.add(DailyHours(
                    employee_id=db_employee.id,
                    date=day_date,
                    hours_worked=round(hours, 4),
                    shift_count=1,
                ))

        results[emp_info["name"].lower()] = {
            "name": emp_info["name"],
            "total_hours": round(total_hours, 4),
            "days_worked": len(daily_hours),
            "shift_count": emp_shift_count[emp_id],
        }

    db.commit()
    return results


def get_monthly_hours_summary(db: Session, year: int, month: int) -> dict:
    """
    Get aggregated hours summary for a month from the database.
    Returns a dict keyed by lowercase employee name.
    """
    from calendar import monthrange
    _, num_days = monthrange(year, month)

    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, num_days).date()

    hours_records = db.query(DailyHours).filter(
        DailyHours.date >= start_date,
        DailyHours.date <= end_date,
    ).all()

    # Aggregate by employee
    emp_data = defaultdict(lambda: {"total_hours": 0.0, "days_worked": set(), "shift_count": 0})
    for record in hours_records:
        employee = db.query(Employee).filter(Employee.id == record.employee_id).first()
        if employee:
            key = employee.name.lower()
            emp_data[key]["name"] = employee.name
            emp_data[key]["total_hours"] += record.hours_worked
            emp_data[key]["days_worked"].add(record.date)
            emp_data[key]["shift_count"] += record.shift_count

    # Convert sets to counts
    result = {}
    for key, data in emp_data.items():
        result[key] = {
            "name": data["name"],
            "total_hours": round(data["total_hours"], 4),
            "days_worked": len(data["days_worked"]),
            "shift_count": data["shift_count"],
        }

    return result


def _find_db_employee(db: Session, insightful_name: str) -> Optional[Employee]:
    """Find a database employee by their Insightful name."""
    # Try insightful_name field first
    emp = db.query(Employee).filter(
        Employee.insightful_name.ilike(insightful_name),
        Employee.is_active == True,
    ).first()
    if emp:
        return emp

    # Try regular name (case-insensitive)
    emp = db.query(Employee).filter(
        Employee.name.ilike(insightful_name),
        Employee.is_active == True,
    ).first()
    if emp:
        return emp

    # Try first name match
    first_name = insightful_name.split()[0]
    emp = db.query(Employee).filter(
        Employee.name.ilike(f"{first_name}%"),
        Employee.is_active == True,
    ).first()
    return emp


async def _async_sleep(seconds: float):
    """Async sleep for rate limiting."""
    import asyncio
    await asyncio.sleep(seconds)
