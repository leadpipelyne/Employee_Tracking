#!/usr/bin/env python3
"""
Fetch all employee data and shift/attendance data from Insightful API
for February 2026, week by week.
"""

import json
import requests
import time
from datetime import datetime, timezone
from collections import defaultdict

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ind0ZWU3NGNlY2pzZWdzYSIsImFjY291bnRJZCI6Inc4anV0NWhrZWJ5cnAyaSIsIm9yZ2FuaXphdGlvbklkIjoidzl3eGF2X3V4emJ2bm1uIiwidHlwZSI6InVzZXIiLCJ1c2VyVHlwZSI6ImFwaSIsInZlcnNpb24iOjIsImlhdCI6MTc3MjQ1MjEwMywiZXhwIjozMTczMTY4OTQ1MDMsImF1ZCI6WyJQUk9EIl0sImlzcyI6IlBST0QifQ.r4zAQTD4EOlD2Xn21PKrLPAnDKFlZVjDw_emWSQHZ2w"

BASE_URL = "https://app.insightful.io/api/v1"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

# February 2026 date ranges (week by week)
# Feb 1 (Sun) to Feb 28 (Sat)
WEEK_RANGES = [
    ("2026-02-01", "2026-02-07"),  # Week 1: Feb 1-7
    ("2026-02-08", "2026-02-14"),  # Week 2: Feb 8-14
    ("2026-02-15", "2026-02-21"),  # Week 3: Feb 15-21
    ("2026-02-22", "2026-02-28"),  # Week 4: Feb 22-28
]

def date_to_ms(date_str):
    """Convert date string to unix timestamp in milliseconds (start of day UTC)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def date_to_ms_end(date_str):
    """Convert date string to unix timestamp in milliseconds (end of day UTC)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000) + 86400000 - 1  # 23:59:59.999

def fetch_employees():
    """Fetch all employees from the API."""
    print("Fetching employee list...")
    resp = requests.get(f"{BASE_URL}/employee", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    employees = resp.json()
    print(f"  Found {len(employees)} employees")
    return employees

def fetch_shifts_for_week(start_date, end_date):
    """Fetch all shifts for a given date range."""
    start_ms = date_to_ms(start_date)
    end_ms = date_to_ms_end(end_date)
    
    print(f"  Fetching shifts for {start_date} to {end_date}...")
    resp = requests.get(
        f"{BASE_URL}/analytics/shift",
        params={"start": start_ms, "end": end_ms},
        headers=HEADERS,
        timeout=60
    )
    resp.raise_for_status()
    shifts = resp.json()
    print(f"    Got {len(shifts)} shift records")
    return shifts

def main():
    # Step 1: Fetch all employees
    employees = fetch_employees()
    
    # Create employee lookup
    emp_map = {}
    for emp in employees:
        emp_map[emp["id"]] = {
            "id": emp["id"],
            "name": emp["name"],
            "email": emp.get("email", ""),
            "teamId": emp.get("teamId", ""),
            "identifier": emp.get("identifier", ""),
            "deactivated": emp.get("deactivated", 0),
        }
    
    # Save employee map
    with open("/home/ubuntu/employee_map.json", "w") as f:
        json.dump(emp_map, f, indent=2)
    print(f"\nSaved employee map ({len(emp_map)} employees)")
    
    # Step 2: Fetch shifts week by week
    all_shifts = []
    for start_date, end_date in WEEK_RANGES:
        time.sleep(1)  # Rate limiting
        shifts = fetch_shifts_for_week(start_date, end_date)
        all_shifts.extend(shifts)
    
    print(f"\nTotal shifts fetched: {len(all_shifts)}")
    
    # Step 3: Aggregate hours per employee
    emp_hours = defaultdict(float)
    emp_shift_count = defaultdict(int)
    emp_daily_shifts = defaultdict(lambda: defaultdict(float))
    
    for shift in all_shifts:
        emp_id = shift["employeeId"]
        duration_hrs = shift["duration"] / (1000 * 3600)  # ms to hours
        emp_hours[emp_id] += duration_hrs
        emp_shift_count[emp_id] += 1
        
        # Track daily hours
        start_ts = shift.get("startTranslated", shift["start"])
        day_str = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        emp_daily_shifts[emp_id][day_str] += duration_hrs
    
    # Step 4: Build the final data structure
    results = {}
    for emp_id, total_hours in emp_hours.items():
        emp_info = emp_map.get(emp_id, {"name": f"Unknown ({emp_id})", "email": ""})
        results[emp_id] = {
            "id": emp_id,
            "name": emp_info["name"],
            "email": emp_info.get("email", ""),
            "total_hours": round(total_hours, 4),
            "shift_count": emp_shift_count[emp_id],
            "days_worked": len(emp_daily_shifts[emp_id]),
            "daily_hours": {k: round(v, 4) for k, v in sorted(emp_daily_shifts[emp_id].items())}
        }
    
    # Save results
    with open("/home/ubuntu/insightful_feb2026_hours.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"FEBRUARY 2026 HOURS SUMMARY")
    print(f"{'='*80}")
    print(f"{'Name':35s} {'Total Hours':>12s} {'Shifts':>8s} {'Days':>6s}")
    print(f"{'-'*35} {'-'*12} {'-'*8} {'-'*6}")
    
    for emp_id in sorted(results.keys(), key=lambda x: results[x]["name"]):
        r = results[emp_id]
        print(f"{r['name']:35s} {r['total_hours']:>12.2f} {r['shift_count']:>8d} {r['days_worked']:>6d}")
    
    print(f"\nTotal employees with hours: {len(results)}")
    print(f"Data saved to /home/ubuntu/insightful_feb2026_hours.json")

if __name__ == "__main__":
    main()
