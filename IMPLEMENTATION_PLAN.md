# IMPLEMENTATION PLAN: Employee Tracking & Payroll System

## Full Project Roadmap — Written for Non-Technical Review & Approval

**Document Date:** March 2026
**Based on:** Working Python prototype tested against real February 2026 payroll data

---

## How to Read This Plan

This document describes exactly what will be built, in what order, and what you will be able to see and test at each step. It is written for someone who does not write code. Each phase ends with something visible — a screen, a report, or a workflow you can try yourself.

At the end of each phase, there is a section called **"Decisions You Need to Make."** These are choices only you (the business owner / HR lead) can make. Development will pause and wait for your answers before moving to the next phase.

The total project is divided into **6 phases**. Each phase builds on the previous one. Nothing is skipped, and nothing is built out of order.

---

## What Already Exists (Starting Point)

Before any new work begins, here is what we already have:

- **Two working Python scripts** that can pull employee hours from the Insightful time-tracking system and calculate everyone's salary, including deductions and overtime additions. These scripts have been tested against real February 2026 data and produce correct results.
- **A configuration file** that stores all the month-specific settings (working days, thresholds) and exception rules (fixed salary employees, absent employees, name mismatches, manual adjustments).
- **Full documentation** of every business rule, every edge case, and every data source.

What we are building is a proper web application that wraps all of this logic in a user-friendly interface, stores history, and adds new capabilities like anomaly detection and leave management.

---

## PHASE 1: Foundation — The Database and Core Engine

**What happens here:** We build the invisible backbone of the system. This is like laying the foundation and framing of a house — you will not see much on screen yet, but everything that comes later depends on this being done right.

### What Gets Built

1. **The database structure** — A place to permanently store all employee information, salary records, leave balances, exception rules, and every calculation ever run. Right now everything lives in Excel files and a JSON configuration file. After this phase, it lives in a proper database that can be searched, filtered, and audited.

2. **The calculation engine** — The existing salary calculation logic (the part that decides who gets a deduction, who gets overtime pay, and who is unchanged) gets restructured so it can be used by the web application. The math stays exactly the same. The logic stays exactly the same. It is simply reorganized so the web interface can call it.

3. **The Insightful API connector** — The existing script that pulls employee hours from Insightful gets restructured into a reliable, reusable service. It will still fetch data week by week (as required by the API), but it will store the results in the database and handle errors gracefully (for example, if the API is temporarily unavailable, it will retry instead of crashing).

4. **The API layer** — A set of behind-the-scenes endpoints that the web interface will talk to. Think of these as the "verbs" of the system: "get all employees," "run payroll for March," "add an exception," "download the report." You will not interact with these directly — the web interface will.

### What You Will See at the End of Phase 1

A simple test page (not pretty, but functional) where you can:
- See a list of employees pulled from the database
- Trigger a payroll calculation for a specific month
- See the raw calculation results in a table
- Verify that the numbers match exactly what the existing scripts produce for February 2026

This is a **verification checkpoint**. The purpose is to confirm that the new system produces identical results to the tested prototype before we build anything on top of it.

### Decisions You Need to Make

1. **Database choice:** We can start with a lightweight database (SQLite, which requires no separate server) for speed, then move to a more robust one (PostgreSQL) later. Or we can start directly with PostgreSQL. The recommendation is to start with PostgreSQL since that is what we will use in production. Do you agree?

2. **Where will the system be hosted?** On your own server, or on a cloud service (like AWS, Google Cloud, or DigitalOcean)? This affects some early setup decisions.

3. **Who should have access?** Just HR? HR plus management? Do different people need different permission levels? (We will build the login system in Phase 2, but the answer affects database design now.)

---

## PHASE 2: The Login System and Employee Management Screen

**What happens here:** The system gets a real front door.

### What Gets Built

1. **Login screen** — A secure username/password login page. Only authorized people can access the system.

2. **User roles** — At minimum, two roles:
   - **Admin** (full access to everything, can run payroll, change settings)
   - **Viewer** (can see reports and data but cannot change anything)
   You can decide later if you need more roles (e.g., a "Manager" who can approve exceptions but not change salaries).

3. **Employee management screen** — A searchable table showing all employees with their key details:
   - Name, currency, current monthly salary, employment status
   - Their Insightful tracking status (tracked / not tracked / fixed salary)
   - Their current exception status (if any)
   - The ability to add new employees, edit details, or mark someone as inactive

4. **Employee profile page** — Click on any employee's name and see their complete profile:
   - Personal details and salary information
   - History of all payroll calculations they have been included in
   - Current exception rules that apply to them
   - Leave balance summary

### What You Will See at the End of Phase 2

A real web application with:
- A login page where you enter your username and password
- A dashboard-style home page (basic at this stage, will get richer later)
- An "Employees" section where you can browse, search, and edit the employee list
- Click into any employee to see their profile

You should be able to log in, browse employees, and edit basic information. The look and feel will be clean and professional.

### Decisions You Need to Make

1. **Who are the initial users?** Provide the names and email addresses of people who need accounts.

2. **Do you want to log in with email/password, or integrate with an existing system** (like Google accounts)? Email/password is simpler; Google login is more convenient if everyone already uses Google Workspace.

3. **Should employees be able to log in and see their own data?** Or is this strictly an HR-only tool?

---

## PHASE 3: The Monthly Payroll Workflow (The Heart of the System)

**What happens here:** This is the most important phase. It builds the complete monthly payroll workflow that replaces the current manual Excel process.

### What Gets Built

1. **Monthly configuration screen** — A form where HR sets up the month:
   - Select the month and year
   - Enter the number of working days
   - Upload the Salary Sheet (Excel file)
   - Upload the Leave Requests file (Excel file)
   - The system reads these files automatically, extracts the data, and shows a summary of what it found (number of employees, any issues with the files)

2. **Exception management screen** — A tabbed interface with five sections, one for each exception type:
   - **Fixed Salary tab** — A list of employees who receive full pay regardless of hours. Add or remove employees with one click.
   - **Full Month Absent tab** — A list of employees who were not working at all this month. Same add/remove interface.
   - **Name Mappings tab** — A table showing which Salary Sheet names map to which Insightful names. The system will automatically suggest mappings when it detects similar names that do not match exactly.
   - **Manual Hours tab** — A table where you can credit extra hours to specific employees, with a field to record the reason.
   - **Manual Leaves tab** — A table where you can grant extra leave days, with a field to record the reason.

   Exception rules carry forward from month to month automatically (so you do not re-enter fixed salary employees every time), but can be overridden for any specific month.

3. **Calculation and review screen** — This is the screen HR will use most. When you click "Run Calculation":
   - The system pulls the latest hours from Insightful (or uses previously synced data)
   - It processes every employee through the payroll formula
   - It displays a large, color-coded table:
     - **Red rows** = Deduction (employee fell below 165 hours)
     - **Green rows** = Addition / Overtime (employee exceeded 180 hours)
     - **Yellow rows** = OK (no adjustment needed)
     - **Blue rows** = Fixed salary (paid in full, no calculation)
     - **Grey rows** = Full month absent (zero pay)
   - Each row shows: employee name, actual hours, leave credits, total billable hours, status, deduction or addition amount, final salary, and any notes
   - **Inline editing**: HR can adjust manual hours or leave days for any employee directly in the table. The row recalculates instantly without reloading the page.
   - **Unmatched employee warnings**: If the system cannot match an employee's name between the Salary Sheet and Insightful, it highlights that row in orange and prompts HR to create a name mapping.

4. **Finalize and lock** — Once HR is satisfied with all the numbers, they click "Finalize." This:
   - Locks the calculation so it cannot be accidentally changed
   - Records who finalized it and when (audit trail)
   - Generates the Excel report (same multi-sheet format as the current prototype: main salaries, comparison with original, exceptions & config, calculation logic)
   - Makes the report available for download

### What You Will See at the End of Phase 3

The complete payroll workflow, end to end:
1. Log in
2. Go to "Payroll" and select the month
3. Set up the month (working days, upload files)
4. Review or update exceptions
5. Click "Run Calculation" and see the full color-coded results table
6. Make any last-minute adjustments inline
7. Click "Finalize" and download the Excel report
8. Verify that the Excel report matches the format and numbers you are used to seeing

**This is the most critical testing checkpoint.** You should run the March 2026 payroll through the new system and compare the results side by side with your current manual process. Every number should match.

### Decisions You Need to Make

1. **Should the system automatically pull data from Insightful when you start a new month, or should it wait for you to click a button?** Automatic is more convenient; manual gives you more control over when the API is called.

2. **Who can finalize a payroll run?** Should only the Admin role be allowed, or can any HR user finalize?

3. **Should finalized payroll be completely locked, or should an Admin be able to "unlock" and re-run if a mistake is discovered?** If unlocking is allowed, it should be logged as an audit event.

4. **The Excel report currently has 4 sheets. Do you want to add or change anything about the report format?** Now is the best time to ask for adjustments.

---

## PHASE 4: Leave Management and Historical Data

**What happens here:** The system gains the ability to track leave balances over time and builds up a historical record of all payroll runs.

### What Gets Built

1. **Leave management module** — A dedicated section for tracking employee leave:
   - **Leave balance view**: Each employee accrues 2 leave days per month. The system tracks their running balance (how many days they have earned, how many they have used, and how many remain).
   - **Maximum consecutive leave rule**: The system enforces the 5-consecutive-day limit. If someone requests more than 5 days in a row, it flags it for review.
   - **Leave history**: A timeline showing every leave period an employee has taken, with type (sick, casual, etc.), dates, and approval status.
   - **Leave conflict detection**: If an employee's leave records in the Salary Sheet and the Leave Requests file disagree, the system highlights the discrepancy for HR to resolve.

2. **Payroll history** — A screen showing every payroll run ever completed:
   - Month, year, who ran it, when it was finalized
   - Summary statistics (total payroll, total deductions, total additions)
   - Click into any historical run to see the full results table
   - Download the Excel report for any past month
   - Compare two months side by side (e.g., "How did February compare to January?")

3. **Employee salary history** — On each employee's profile page, a timeline showing:
   - Their salary for each month
   - Their hours worked, deductions, and additions over time
   - A simple chart showing their hours trend (are they consistently above or below the threshold?)

### What You Will See at the End of Phase 4

- A "Leave Management" section where you can see everyone's leave balances at a glance
- A "History" section where you can look back at any past payroll run
- On any employee's profile, a history tab showing their payroll track record over time
- Warnings when leave records conflict or when someone exceeds consecutive leave limits

### Decisions You Need to Make

1. **Leave accrual start date:** When should the system start tracking leave balances? From the first month the system goes live, or should we backfill historical data from the Excel files?

2. **Leave types:** The current Leave Requests file includes a "Leave Type" column (Sick Leave, Casual Leave, etc.). Should the system track balances separately by type, or just one overall leave balance?

3. **What should happen when an employee uses more leave than they have accrued?** Should it be blocked, should it show a warning, or should it just be recorded as negative balance?

---

## PHASE 5: Automated Syncing, Anomaly Detection, and Analytics

**What happens here:** The system becomes proactive. Instead of just calculating numbers when asked, it starts watching for problems, syncing data automatically, and providing insights.

### What Gets Built

1. **Automated daily sync with Insightful** — A scheduled background task that runs once per day (for example, at 2 AM) and pulls the latest employee hours from the Insightful API. This means that when HR opens the system on any given day, the hours data is already fresh and up to date, without needing to wait for it to load.

2. **Anomaly detection engine** — The system automatically scans for suspicious patterns and flags them for review:
   - **Compensation abuse**: If an employee repeatedly submits manual hour adjustments in 3+ consecutive months, or if manual hours exceed 10% of actual hours.
   - **Leave conflicts**: An employee shows Insightful hours on an approved leave day (suspicious).
   - **Absent without notice**: No hours and no leave on a working day.
   - **Threshold gaming**: Employees whose hours consistently land just barely above the 165-hour threshold month after month.
   - **High cost-per-hour**: An employee whose effective hourly cost is more than 50% above the team average.

3. **Dashboard with analytics** — The home page becomes a real dashboard showing:
   - Current month status: how many days remain, projected payroll based on hours so far
   - Anomaly alerts: any flags that need HR attention
   - Quick statistics: total headcount, active vs. inactive employees, average hours worked
   - Currency breakdown: total payroll cost broken down by INR, GBP, AED, and USD
   - Trend charts: company-wide hours trend, deduction/addition trends over the past 6 months

4. **Notification system** — The system can send alerts when:
   - The daily sync completes (or fails)
   - An anomaly is detected
   - It is time to run payroll (e.g., 3 days before month end)
   - An employee's hours are trending dangerously low mid-month

### What You Will See at the End of Phase 5

- A rich dashboard when you first log in, showing the health of the current month at a glance
- An "Anomalies" section with flagged issues and explanations of why each was flagged
- Hours data that is always up to date without manual effort
- Charts and trend lines showing payroll patterns over time
- Alerts for anything that needs your attention

### Decisions You Need to Make

1. **What time should the daily sync run?** It needs to happen during off-hours. Suggested: 2:00 AM in your primary time zone.

2. **Anomaly sensitivity:** Should the system flag every possible issue (more alerts, some may be harmless) or only flag high-confidence issues (fewer alerts, but might miss some things)? We can tune this over time.

3. **Who receives notifications?** Just the primary HR administrator, or should multiple people get alerts?

4. **What is your primary currency for cost analysis?** When comparing total payroll costs across currencies, what should the base currency be?

---

## PHASE 6: Reporting, Audit Trail, and Polish

**What happens here:** The system gets its finishing touches — comprehensive reporting, a complete audit trail, and overall polish.

### What Gets Built

1. **Advanced reporting** — New report types beyond the standard monthly payroll report:
   - **Annual summary report**: A 12-month overview showing each employee's salary, hours, deductions, and additions for the entire year.
   - **Cost analysis report**: Total payroll costs by department, currency, and month, with charts.
   - **Exception usage report**: How often each exception type is used, which employees are most frequently on exception lists.
   - **Anomaly report**: A summary of all anomalies detected, which were resolved, and which are still open.
   - All reports available as Excel downloads and on-screen views.

2. **Complete audit trail** — Every action in the system is recorded:
   - Who logged in and when
   - Who changed an exception rule, what they changed, and when
   - Who ran a payroll calculation, who finalized it
   - Who downloaded a report
   - Who edited an employee record and what they changed
   - This audit log is searchable and filterable

3. **Multi-currency display improvements** — Throughout the system, amounts are shown with proper currency formatting:
   - INR amounts show the Rupee symbol
   - GBP, AED, USD show their respective symbols
   - Summary totals can show amounts in each currency separately, or converted to a single base currency for comparison

4. **Overall polish and usability improvements** —
   - Loading indicators so you always know when the system is working
   - Error messages in plain English (not technical jargon)
   - Mobile-friendly layout so basic information can be viewed on a phone
   - Help tooltips explaining what each field means

### What You Will See at the End of Phase 6

The complete, finished system:
- Everything from Phases 1 through 5, fully polished
- A "Reports" section with multiple report types you can generate and download
- An "Audit Log" section where you can see a complete history of who did what
- Proper currency formatting everywhere
- A system that feels professional and finished

### Decisions You Need to Make

1. **Audit retention:** How long should audit records be kept? Forever? One year? Three years? (Recommendation: keep everything forever; storage is cheap and the data is small.)

2. **Report branding:** Should the Excel reports include your company logo and branding, or keep them plain?

3. **Any additional reports?** This is the best time to request any report format you have wished for but never had.

---

## Summary of All 6 Phases

| Phase | What It Delivers | What You Can Test |
|-------|-----------------|-------------------|
| Phase 1 | Database, calculation engine, API layer | Verify numbers match the existing prototype |
| Phase 2 | Login, employee management, profiles | Log in, browse and edit employees |
| Phase 3 | Complete payroll workflow | Run a full month's payroll end-to-end |
| Phase 4 | Leave management, payroll history | Track leave balances, view past months |
| Phase 5 | Auto-sync, anomaly detection, dashboard | See flags, charts, and daily-updated data |
| Phase 6 | Reports, audit trail, polish | Generate reports, review audit logs |

---

## What Happens Between Phases

At the end of each phase:
1. You receive a working version of the system to test
2. You try every new feature and tell us what is right, what is wrong, and what needs to change
3. We fix anything that is not right before starting the next phase
4. You answer the "Decisions You Need to Make" questions for the next phase
5. We begin the next phase only after you approve

This means you are never surprised. You see progress regularly, and you have the ability to change direction at every checkpoint.

---

## Risks and What We Will Do About Them

| Risk | What We Will Do |
|------|----------------|
| The Insightful API changes or goes down | The system stores all synced data locally. HR can still run payroll using the most recent data and manually enter any missing hours. |
| Excel file formats change | The system validates uploaded files before processing. If the layout changes, it tells you exactly what is different instead of producing wrong numbers. |
| New exception types are needed | The exception system is designed to be extensible. Adding a new type is straightforward. |
| Employee count grows significantly | The system is designed to handle hundreds of employees, not just the current 44. |
| Someone makes a mistake in payroll | The finalize-and-lock system, comparison sheets, and audit trail make it easy to catch and correct errors. |

---

## Glossary of Terms Used in This Plan

| Term | What It Means |
|------|---------------|
| **Threshold (165 hours)** | The minimum total hours an employee must work in a month (including leave credits) to avoid a salary deduction. Based on 20 working days at 8 hours 15 minutes per day (with 45-minute lunch grace). |
| **Expected hours (180 hours)** | The full expected hours in a month. Based on 20 working days at 9 hours per day. Hours above this earn overtime. |
| **Billable hours** | Actual hours worked (from Insightful) plus leave credits plus any manual hour adjustments. This is the number compared against the threshold. |
| **Deduction** | Money subtracted from salary when billable hours fall below 165. Calculated from the 180-hour mark, not 165. |
| **Addition** | Extra money added to salary when billable hours exceed 180 (overtime pay). |
| **Fixed salary** | An exception where the employee receives full pay regardless of hours. |
| **Name mapping** | A link between an employee's name in the Salary Sheet and their name in Insightful, when they do not match exactly. |
| **Cron job** | An automated task that runs on a schedule (like an alarm clock for the computer). Used for the daily data sync. |
| **Audit trail** | A permanent record of every action taken in the system, including who did it and when. |
| **API** | A way for two computer systems to talk to each other. In this case, how our system gets hours data from Insightful. |

---

*This plan is based on the working prototype code, the build brief (CLAUDE_BUILD_BRIEF.md), the exception rules guide (EXCEPTIONS_GUIDE.md), the data & API reference (DATA_AND_API.md), and the Manus AI gap analysis — all tested against real February 2026 payroll data.*
