Timetracking and Attendance in ERPNext, integrated with Jira

## Who is this for?

Companies that use Atlassian Jira for project management and ERPNext for time tracking and billing.

## Features

- Allows logging of miscellaneous time, project time, breaks and paid breaks
- Optional **Activity Type** on each project time log (defaults to `"Default"`)
- Creates separate **Timesheet** entries when the same project is logged with different activity types
- Resolves billing and costing rates from **Activity Cost**, then **Project**, then **Activity Type**
- Optional project-specific **Activity Cost** records for different rates per project
- Allows to set a percentage of working time as billable time in a **Working Time Log**
- Rounds billable time to 5 minutes
- Fetches issue titles from Jira (used as time log description)
- Creates ERPNext **Timesheets**
- Creates ERPNext **Attendances**
- Whole-day project timesheets (single 8-hour **Timesheet** merged from multiple logs)
- Report of actual vs. expected working time per Employee
- Sends email reminders to employees for submitting their draft working time entries
    - If a draft working time entry is older than 3 days, and
    - on the last working day of the month
- **Working Time Policy** enforcement per employee, including:
    - Maximum productive time per day
    - Mandatory break requirements based on productive time thresholds
    - Minimum rest time between days
    - Blocked weekdays
    - Holiday blocking (based on the employee's holiday list)

## Activity types and billing rates

This section explains how **Working Time** turns your daily logs into **Timesheet** rows with the correct rates.

### Activity Type on time logs

When a **Working Time Log** row is linked to a **Project**, you can choose an **Activity Type** (for example `"Default"` or `"Support"`). If you leave it empty, `"Default"` is used automatically.

Different activity types on the same day produce **separate Timesheet entries**, even when project, task, and Jira key are the same. That lets you bill or cost the same project at different rates within one day.

### How rates are chosen

When you submit **Working Time**, each **Timesheet** line gets a billing rate and a costing rate. They are resolved independently:

**Billing rate** (what the customer is charged):

1. **Activity Cost** for this employee, activity type, and project (if a matching record exists)
2. Otherwise **Activity Cost** for the same employee and activity type without a project
3. Otherwise the **Project** billing rate per hour
4. Otherwise the default rates on the **Activity Type**
5. Otherwise `0`

**Costing rate** (internal employee cost):

1. **Activity Cost** for this employee, activity type, and project (if a matching record exists)
2. Otherwise **Activity Cost** for the same employee and activity type without a project
3. Otherwise the default rates on the **Activity Type**
4. Otherwise `0`

Whole-day **Timesheet** entries use the **Project** billing rate per day (or per hour) for billing, but still use **Activity Cost** for costing.

### Project-specific Activity Cost

**Activity Cost** has an optional **Project** field. Use it when one employee should have different rates on different projects while keeping the same activity type.

Example:

| Employee | Activity Type | Project | Billing rate | Costing rate |
|----------|---------------|---------|--------------|--------------|
| Jane Doe | Default | *(empty)* | 100 | 45 |
| Jane Doe | Default | Client A | 120 | 50 |

When Jane logs time on Client A, the project-specific row is used. On any other project, the row without a project applies.

Each combination of employee, activity type, and project may exist only once. You can have one generic record (no project) and additional records for specific projects.

After upgrading an existing site, run `bench migrate` so the **Project** field is added to **Activity Cost**.

### Whole-day project

If **Working Time** has a **Whole Day Project** set, all logs on that project are merged into one 8-hour **Timesheet** when you submit. Every log on that project must use the **same activity type** (or all default to `"Default"`). Mixed activity types are rejected with an error instead of silently using only the first log's type.

## Setup

- Install this app

   ```bash
   bench get-app https://github.com/alyf-de/working_time
   bench install-app working_time
   ```

- Create a **Jira Site**, enter your _Site URL_, _Username_ and a non-scoped _API Token_
  (scoped API tokens are not supported)
- Enable _Ignore Employee Time Overlap_ and _Ignore User Time Overlap_ in **Projects Settings**
- Open or create an ERPNext **Project**
    - Link it to your **Jira Site**
    - Set the _Billing Rate per Hour_ (and optionally _Billing Rate per Day_ for whole-day billing)
- Create **Activity Type** records if you need types other than `"Default"` (installed automatically on first install)
- Create **Activity Cost** records for your **Employees**
    - One row per employee and activity type without a project for your standard rates
    - Optional extra rows with **Project** set for project-specific rates
- Optionally assign a **Working Time Policy** on each **Employee**
- Create your first **Working Time**
    - Add a time log with description,
    - Add a time log and mark it as a break,
    - Add a time log and link it to a _Project_, Jira issue _Key_, and optionally _Activity Type_
- Submit your **Working Time** and review the draft **Timesheets** created for that day

### Quick checklist for rates

1. Create **Activity Type** records (e.g. `"Default"`, `"Support"`).
2. For each employee, create **Activity Cost** with activity type `"Default"` and your standard hourly rates.
3. Add project-specific **Activity Cost** rows only where rates differ from the standard.
4. Set **Billing Rate per Hour** on each **Project** as a fallback when no **Activity Cost** billing rate applies.
5. Submit a test **Working Time** with two logs on the same project but different activity types; confirm two **Timesheets** with the expected rates.

## Time Fields

**Working Time** separates productive time, break time and paid time:

- _Productive Time_ (`productive_time`) is the total duration of logs that are not marked as breaks.
- _Break Time_ (`break_time`) is the total duration of logs marked as breaks, including paid breaks.
- _Paid Break Time_ (`paid_break_time`) is the total duration of break logs where _Paid_ (`is_paid_break`) is enabled.
- _Paid Working Time_ (`working_time`) is the paid total: _Productive Time_ plus _Paid Break Time_. Number cards, stats and reports use this field as the paid working time total.
- _Project Time_ (`project_time`) and _Billable Time_ (`billable_time`) are calculated from non-break project logs.

In a **Working Time Log**, mark _Break_ (`is_break`) for any physical break. Regular working logs are paid by default and should not be marked as breaks. Regular breaks are unpaid by default. Use _Paid_ (`is_paid_break`) only for exceptional break rows that should count toward paid working time, such as mandatory but passive travel time.

**Working Time Policy** restrictions use _Productive Time_ for maximum time and threshold checks, while mandatory break requirements use _Break Time_. This means paid breaks count as paid time, but do not increase productive time for policy restrictions.

German users may refer to [this article](https://www.kanzlei-chevalier.de/blog/dienstreise-als-arbeitszeit) for more information.

## Further Reading

Want to add pretty time logs to your invoice? Check out our [print formats](https://github.com/alyf-de/erpnext_druckformate).

## License

ERPNext extension "Working Time": Timetracking and Attendance in ERPNext, integrated with Jira.
Copyright (C) 2024 ALYF GmbH and contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
