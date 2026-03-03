# Data Schema & API Reference

This document details the structure of the input data files and the external Insightful API used by the system.

## 1. Data Schemas

The system relies on two primary Excel files for salary and leave information.

### 1.1. Salary & Main Leave Sheet (`February-26Salaries.xlsx`)

This file contains two critical sheets:

#### `Salaries` Sheet

This is the master list of employees and their salary details.

| Column | Header | Description |
| :--- | :--- | :--- |
| A | Employee Name | The full name of the employee. **This is the primary key.** |
| B | Salary For February 2026 | The gross monthly salary amount. |
| D | Deduction | (Original manual value) The amount to be deducted. |
| E | Addition | (Original manual value) The amount to be added (e.g., overtime). |
| G | Reimbursement | Any fixed reimbursement amount to be added to the final pay. |
| I | Hours | (Original manual value) The total hours worked. |
| M | Currency | The currency of the salary (e.g., INR, GBP, AED). |

#### `Leaves` Sheet

This sheet within the same file tracks approved leave days.

| Column | Header | Description |
| :--- | :--- | :--- |
| A | Name | The name of the employee. |
| C | Leaves to be considered | The number of approved leave days to credit for the month. |
| E | Status | The status of the leave request (e.g., Approved). |

### 1.2. External Leave Requests Sheet (`LeaveRequests.xlsx`)

This file is a secondary source for leave information and may contain more up-to-date requests.

#### `Sheet1`

| Column | Header | Description |
| :--- | :--- | :--- |
| B | Employee Name | The name of the employee requesting leave. |
| C | Leave Type | The type of leave (e.g., Sick Leave, Casual Leave). |
| D | Start Date | The start date of the leave period. |
| E | End Date | The end date of the leave period. |
| F | No of Days | The total number of leave days requested. |
| G | Status | The approval status of the request. **Only "Approved" requests should be counted.** |

**Note:** The system should be able to read from both leave sources and consolidate the data, avoiding double-counting.

## 2. Insightful API Reference

The system fetches real-time employee work hours from the Insightful (formerly WorkPulse) API.

- **Base URL:** `https://api.insightful.io`
- **Authentication:** `Bearer Token`
  - A JWT token is passed in the `Authorization` header.
  - `Authorization: Bearer <YOUR_JWT_TOKEN>`

### Key Endpoints

#### Get Employee List

- **Endpoint:** `GET /v1/employee`
- **Purpose:** To retrieve a list of all active employees in the Insightful organization. This is used to map employee names to their Insightful IDs.
- **Response Fields:**
  - `id`: The unique identifier for the employee.
  - `name`: The full name of the employee.
  - `email`: The employee's email address.

#### Get Employee Shifts

- **Endpoint:** `GET /v1/analytics/shift`
- **Purpose:** To retrieve all work shifts for all employees within a specified time range. This is the core endpoint for fetching `Actual Hours`.
- **Query Parameters:**
  - `from`: The start of the time range in **Unix timestamp** format (e.g., `1769983200` for Feb 1, 2026).
  - `to`: The end of the time range in **Unix timestamp** format.
- **Pagination Strategy:** Due to API limitations and to ensure reliability, data should be fetched **week by week** for the entire month, rather than making a single request for the whole month.
- **Response Fields:**
  - `employeeId`: The ID of the employee who worked the shift.
  - `duration`: The length of the work shift in **seconds**. This needs to be converted to hours (`duration / 3600`).
