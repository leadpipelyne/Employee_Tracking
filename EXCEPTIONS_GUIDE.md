# Exceptions & Manual Adjustments Guide

This document explains the exception system and how to configure it for each month.

## 1. Overview

Not every employee follows the standard hour-based calculation. The system supports four types of exceptions, all configured in `src/config.json` under the `"exceptions"` key. These must be reviewed and updated by HR before running the calculation each month.

## 2. Exception Types

### 2.1. Fixed Salary Employees

These employees receive their full gross salary regardless of the hours they have logged in Insightful. This category typically includes contractors, invoice-based workers, or employees whose work is not tracked through the standard system.

**How it works:** The system skips the entire deduction/addition calculation and pays the full salary amount from the Salary Sheet.

**Current list (as of February 2026):**

| Employee | Reason |
| :--- | :--- |
| FLOID | Fixed contract |
| CARLA | Fixed contract |
| Atisha | Fixed contract |
| Sneha | Fixed contract |
| VINITA SHRIWASTAV | Fixed contract |
| Rakhi Devi | Fixed contract |
| Ronak | Invoice-based payment |

**To update:** Add or remove names from the `"fixed_salary"` array in `config.json`.

### 2.2. Full Month Absent

These employees were not working at all during the entire month. The system applies a 100% deduction, resulting in a final salary of zero.

**Current list (as of February 2026):**

| Employee | Reason |
| :--- | :--- |
| Jyoti | On extended leave, not working in February |

**To update:** Add or remove names from the `"full_month_absent"` array in `config.json`.

### 2.3. Name Mappings

Sometimes an employee's name in the Salary Sheet does not exactly match their name in the Insightful system. Without a mapping, the system cannot find their hours and would incorrectly show them as having zero hours worked.

**Current mappings (as of February 2026):**

| Salary Sheet Name | Insightful Name |
| :--- | :--- |
| Ajith Kumar | Ajit Kumar |

**To update:** Add new key-value pairs to the `"name_mappings"` object in `config.json`. The key is the Salary Sheet name and the value is the Insightful name (lowercase).

### 2.4. Manual Hour Adjustments

In some cases, an employee may have performed work that was not tracked by Insightful (e.g., client meetings, offline work). HR can manually credit additional hours to their total before the calculation runs.

**Current adjustments (as of February 2026):**

| Employee | Extra Hours | Reason |
| :--- | :--- | :--- |
| Heena | 17 hours | Untracked work hours |

**To update:** Add new key-value pairs to the `"manual_hour_adjustments"` object in `config.json`. The key is the employee name and the value is the number of hours to add.

### 2.5. Manual Leave Adjustments

Beyond the leaves tracked in the Leave Requests sheet, HR may grant additional leave days for special circumstances (e.g., marriage, bereavement). Each leave day adds 9 hours of credit.

**Current adjustments (as of February 2026):**

| Employee | Extra Leave Days | Reason |
| :--- | :--- | :--- |
| Chandni | 5 days | Marriage leave |
| Heena | 3 days | Had remaining leave balance |

**To update:** Add new key-value pairs to the `"manual_leave_adjustments"` object in `config.json`. The key is the employee name and the value is the number of extra leave days.

## 3. Monthly Checklist for HR

Before running the salary calculation each month, HR should complete the following checklist:

1. Update `"month"`, `"year"`, and `"working_days"` in `config.json`.
2. Upload the latest Salary Sheet and Leave Requests file to the `data/` directory.
3. Review and update the `"fixed_salary"` list — has anyone joined or left this category?
4. Review and update the `"full_month_absent"` list — is anyone on extended leave this month?
5. Check for any new name mismatches and add them to `"name_mappings"`.
6. Gather any manual hour adjustment requests and add them to `"manual_hour_adjustments"`.
7. Gather any special leave grants and add them to `"manual_leave_adjustments"`.
8. Run the calculation.
9. Review the output report before distributing.
