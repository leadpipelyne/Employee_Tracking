# Build Brief for Claude: HR Payroll Automation System

**Purpose of this document:** This is a complete specification written specifically for Claude (or any AI developer) to build a production-grade web application. It contains every piece of business logic, edge case, and data structure discovered during the prototyping phase. The working reference code in `/src` has been tested against real data and produces correct results.

---

## Part 1: What You Are Building

A web application that automates the monthly salary calculation process for a company with approximately 44 employees. The system replaces a manual Excel-based workflow where HR currently spends hours each month pulling data from multiple sources, cross-referencing it, and calculating deductions and additions by hand.

The application must integrate three data sources, apply a specific set of business rules, handle exceptions, and produce a final salary report in Excel format.

---

## Part 2: The Complete Business Logic

### 2.1. Constants and Thresholds

Each month, the following parameters are configured:

| Parameter | Description | Example (Feb 2026) |
| :--- | :--- | :--- |
| Working Days | Number of business days in the month | 20 |
| Full Day Hours | The total expected hours per day | 9 |
| Threshold Hours/Day | Minimum productive hours (after 45-min lunch relief) | 8.25 (i.e., 8h 15m) |
| Monthly Threshold | Working Days × 8.25 | 165 hours |
| Monthly Total Expected | Working Days × 9 | 180 hours |
| Paid Holidays/Month | Standard paid holidays included | 2 days |

### 2.2. The Core Calculation (Per Employee)

For each employee, the system computes:

**Step 1 — Gather Data:**
- `Actual Hours` = Total work hours from Insightful API for the month.
- `Leave Hours` = (Approved leave days from Leave Sheet + Manual leave adjustments) × 9.
- `Manual Hours` = Any manually credited untracked hours.
- `Total Billable Hours` = Actual Hours + Leave Hours + Manual Hours.

**Step 2 — Determine Status:**

```
IF Total Billable Hours < Monthly Threshold (165):
    STATUS = "DEDUCT"
    
ELIF Total Billable Hours > Monthly Total Expected (180):
    STATUS = "ADDITION"
    
ELSE (between 165 and 180, inclusive):
    STATUS = "OK" — no adjustment
```

**Step 3 — Calculate Amount:**

```
Hourly Rate = Monthly Salary / Monthly Total Expected

IF STATUS == "DEDUCT":
    Shortfall = Monthly Total Expected - Total Billable Hours
    Deduction = Shortfall × Hourly Rate
    
    CRITICAL RULE: The shortfall is measured from the FULL 9-hour day (180 hrs),
    NOT from the 8h15m threshold (165 hrs). The 45-minute lunch relief is a grace
    that is LOST when the threshold is not met.

IF STATUS == "ADDITION":
    Excess = Total Billable Hours - Monthly Total Expected
    Addition = Excess × Hourly Rate
```

**Step 4 — Final Salary:**
```
Final Salary = Gross Salary - Deduction + Addition
Total Pay = Final Salary + Reimbursement (if any)
```

### 2.3. Exception Types

The system must support these exception categories, all configurable via a UI or config file:

**Fixed Salary:** Employee receives full salary regardless of hours. No calculation is performed. Typical for contractors, invoice-based workers, or employees not tracked in Insightful.

**Full Month Absent:** Employee was not working at all during the month. Full deduction is applied (final salary = 0).

**Name Mappings:** Maps an employee's name from the Salary Sheet to a different name in Insightful. This is necessary because some employees are registered under slightly different names in the two systems (e.g., "Ajith Kumar" in salary sheet vs "Ajit Kumar" in Insightful).

**Manual Hour Adjustments:** Adds extra hours to an employee's total for work not tracked by Insightful (e.g., offline meetings, client visits). These hours are added to `Total Billable Hours` before the calculation.

**Manual Leave Adjustments:** Adds extra leave days beyond what is in the Leave Sheet (e.g., marriage leave, compassionate leave). Each day adds 9 hours to `Total Billable Hours`.

---

## Part 3: Data Sources

### 3.1. Insightful API

**Base URL:** `https://app.insightful.io/api/v1`

**Authentication:** Bearer token in the Authorization header.

**Endpoint 1 — Employee List:**
```
GET /v1/employee
Response: Array of { id, name, email, teamId, deactivated }
```

**Endpoint 2 — Work Shifts:**
```
GET /v1/analytics/shift?start={unix_ms}&end={unix_ms}
Response: Array of { employeeId, duration (in milliseconds), start, startTranslated }
```

**Critical implementation detail:** Data MUST be fetched week by week for the month, not in a single request. The API has rate limits (300 requests/minute) and may not return complete data for large date ranges. Add a 1-second delay between requests.

**Duration conversion:** `hours = duration / (1000 × 3600)` (duration is in milliseconds).

### 3.2. Salary Sheet (Excel)

The Salary Sheet is an `.xlsx` file with a sheet named `Salaries`. The relevant columns are:

| Column | Index | Content |
| :--- | :--- | :--- |
| A | 0 | Employee Name (primary key) |
| B | 1 | Gross Monthly Salary |
| G | 6 | Reimbursement amount |
| M | 12 | Currency (INR, GBP, AED, etc.) |

The same file also contains a `Leaves` sheet:

| Column | Index | Content |
| :--- | :--- | :--- |
| A | 0 | Employee Name |
| C | 2 | Number of leave days to consider |
| E | 4 | Status |

**Note:** Some employee names contain invisible Unicode characters (e.g., `\u2060` word joiner). The system must strip these before matching.

### 3.3. Leave Requests Sheet (Excel)

A separate `.xlsx` file with leave request details:

| Column | Index | Content |
| :--- | :--- | :--- |
| B | 1 | Employee Name |
| C | 2 | Leave Type |
| D | 3 | Start Date |
| E | 4 | End Date |
| F | 5 | Number of Days |
| G | 6 | Status (only count "Approved") |

---

## Part 4: Name Matching Algorithm

Matching employee names across the three data sources is one of the trickiest parts of the system. The algorithm should follow this priority order:

1. **Explicit mapping:** Check the name mappings table first.
2. **Exact match (case-insensitive):** Direct string comparison.
3. **First name match:** If only one employee in Insightful starts with the same first name.
4. **Last name match:** If only one employee in Insightful contains the same last name.
5. **Partial match:** If one name is a substring of the other.
6. **No match:** Flag the employee for manual review.

The web application should highlight unmatched employees and allow HR to create new mappings on the spot.

---

## Part 5: Recommended Tech Stack

For a production system, the recommended architecture is:

**Option A — Full Web Application (Recommended):**
- **Backend:** Python with FastAPI. The core calculation logic is already written in Python and tested.
- **Frontend:** React with TypeScript and a component library (Ant Design or Material-UI).
- **Database:** SQLite or PostgreSQL for storing monthly configurations, exception lists, and historical reports.
- **File Storage:** Local filesystem or S3 for Excel files.

**Option B — Simpler CLI + Config Approach:**
- A Python CLI tool that reads from `config.json` and the Excel files, runs the calculation, and outputs the report.
- Suitable if the team is comfortable editing JSON files and running scripts.

---

## Part 6: Application Screens (for Option A)

### Screen 1: Dashboard
A summary view showing the current month's status, quick stats (total employees, deductions, additions), and links to the main workflow.

### Screen 2: Monthly Configuration
A form to set the month, year, working days, and upload the Salary Sheet and Leave Requests files. The Insightful API token should be stored securely.

### Screen 3: Exception Management
A tabbed interface with sections for each exception type. HR can add/remove employees from the fixed salary list, manage name mappings, and enter manual adjustments. This should be persistent across months (with the ability to override per month).

### Screen 4: Calculation & Review (Most Critical)
This is the heart of the application. When HR clicks "Run Calculation":

1. The system fetches data from all three sources.
2. It processes each employee one by one, applying the business logic.
3. It displays a table with all results, color-coded by status (red for deductions, green for additions, yellow for OK, blue for fixed, grey for absent).
4. **HR can make inline adjustments** — adding manual hours or leave days for specific employees. The row should recalculate in real-time.
5. Once satisfied, HR clicks "Finalize" to lock the results and generate the Excel report.

### Screen 5: Report History
A list of all previously generated reports with download links.

---

## Part 7: The Output Report

The final Excel report should contain four sheets:

**Sheet 1 — "Monthly Salaries":** The main report with columns for Employee Name, Currency, Monthly Salary, Actual Hours, Days Worked, Leaves Considered, Leave Hours Credit, Total Billable Hours, Status, Deduction, Addition, Salary After Adjustment, Reimbursement, Total Pay, Hourly Rate, Insightful Match, and Notes. Color-coded rows by status.

**Sheet 2 — "Comparison with Original":** A side-by-side comparison of the original Excel sheet values vs. the newly calculated values, with significant differences highlighted.

**Sheet 3 — "Exceptions & Config":** Documents all exception rules and configuration parameters used for that month's calculation, providing a complete audit trail.

**Sheet 4 — "Calculation Logic":** A plain-English explanation of the deduction/addition formula, so anyone reviewing the report can understand how the numbers were derived.

---

## Part 8: Reference Implementation

The `/src` directory contains the following tested, working code:

| File | Purpose |
| :--- | :--- |
| `fetch_insightful_data.py` | Pulls employee list and shift data from the Insightful API, week by week, and saves it as JSON. |
| `calculate_salaries.py` | Reads the JSON hours data, salary sheet, and leave data. Applies all business logic and exceptions. Generates the final multi-sheet Excel report. |
| `config.json` | The configuration file with all parameters, exception lists, and manual adjustments for February 2026. |
| `config.template.json` | A clean template for new months (safe to commit to Git). |

These scripts have been tested against real February 2026 data and produce correct results. Use them as the foundation for the production system.

---

## Part 9: Key Learnings from Prototyping

These are important edge cases and lessons discovered during the prototyping phase that must be carried forward:

1. **The Insightful API returns shift durations in milliseconds**, not seconds or hours. Always divide by `(1000 × 3600)` to get hours.

2. **Data must be fetched week by week.** A single API call for the full month may return incomplete data.

3. **Employee names are inconsistent across systems.** The name matching algorithm must be robust and handle case differences, extra spaces, and Unicode artifacts.

4. **Some employees have very low salaries (e.g., GBP 13, GBP 14).** These are likely part-time or hourly workers. The calculation still applies to them, but the resulting deductions are very small.

5. **The "Leaves" sheet in the Salary file and the separate "LeaveRequests" file may contain overlapping data.** The system should use the Leaves sheet from the Salary file as the primary source and cross-reference with the LeaveRequests file for additional context.

6. **Reimbursements are added after all deduction/addition calculations.** They are never subject to deduction.

7. **The deduction is always calculated from the full 9-hour day (180 hrs), not from the 8h15m threshold (165 hrs).** This is the single most important business rule and the most common source of confusion.
