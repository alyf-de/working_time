Timetracking and Attendance in ERPNext, integrated with Jira

## Features

- Allows logging of miscellanous time, project time and breaks
- Allows to set a percentage of working time as billable time in a Working Time Log
- Rounds billable time to 5 minutes
- Fetches issue titles from Jira (used as time log description)
- Creates ERPNext **Timesheets**
- Creates ERPNext **Attendances**

## Setup

- Install this app

   ```bash
   bench get-app https://github.com/alyf-de/working_time
   bench install-app working_time
   ```

- Create a **Jira Site**, enter your _Site URL_, _Username_ and _API Token_
- Open or create an ERPNext **Project**
    - Link it to your **Jira Site**
    - Set the _Billing Rate per Hour_
- Create **Activity Cost** records for your **Employees** (_Activity Type_: "Default")
- Create your first **Working Time**
    - Add a time log with description,
    - Add a time log and mark it as a break,
    - Add a time log and link it to a _Project_ and Jira issue _Key_
- Submit your **Working Time**
