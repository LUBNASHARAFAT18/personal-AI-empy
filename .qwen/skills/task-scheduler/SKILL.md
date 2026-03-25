---
name: task-scheduler
description: |
  Basic scheduling via cron (Linux/Mac) or Task Scheduler (Windows) for
  recurring AI Employee tasks. Supports daily briefings, periodic checks,
  scheduled postings, and automated reports.
---

# Task Scheduler

Schedule recurring tasks for your AI Employee.

## Overview

The Task Scheduler integrates with your operating system's native scheduling system to run AI Employee tasks automatically at specified times.

## Supported Schedulers

| OS | Scheduler | Command |
|----|-----------|---------|
| **Windows** | Task Scheduler | `schtasks` |
| **Linux** | cron | `crontab` |
| **macOS** | cron or launchd | `crontab` |

## Usage

### Windows (Task Scheduler)

```bash
# Install daily briefing task (runs at 8 AM every day)
python task_scheduler.py D:\personal-AI-empy\AI_Employee_Vault --install --task daily-briefing --time 08:00

# Install weekly audit (runs every Monday at 9 AM)
python task_scheduler.py D:\personal-AI-empy\AI_Employee_Vault --install --task weekly-audit --day monday --time 09:00

# List installed tasks
python task_scheduler.py D:\personal-AI-empy\AI_Employee_Vault --list

# Remove a task
python task_scheduler.py D:\personal-AI-empy\AI_Employee_Vault --remove --task daily-briefing
```

### Linux/Mac (cron)

```bash
# Install daily briefing task
python task_scheduler.py /path/to/AI_Employee_Vault --install --task daily-briefing --time 08:00

# View crontab entry
python task_scheduler.py /path/to/AI_Employee_Vault --show-crontab

# Remove task
python task_scheduler.py /path/to/AI_Employee_Vault --remove --task daily-briefing
```

## Predefined Tasks

### Daily Briefing

Generates a daily summary in Dashboard.md every morning.

**Schedule:** Daily at 8:00 AM

**Output:**
- Yesterday's completed tasks
- Today's priorities
- Pending approvals count
- Financial summary

### Weekly Audit

Comprehensive weekly business review.

**Schedule:** Every Monday at 9:00 AM

**Output:**
- Week's revenue
- Completed tasks summary
- Bottlenecks identified
- Subscription audit

### Gmail Check

Periodic Gmail monitoring.

**Schedule:** Every 2 hours during business hours

**Output:**
- New email action files
- Priority flagging

### Social Media Post

Scheduled LinkedIn posting.

**Schedule:** Configurable (e.g., 9 AM, 3 PM)

**Output:**
- Posts approved content
- Tracks engagement

## Custom Tasks

Create custom scheduled tasks:

```bash
# Custom task with Python script
python task_scheduler.py D:\personal-AI-empy\AI_Employee_Vault \
  --install \
  --task custom \
  --script watchers/my_custom_task.py \
  --schedule "0 */4 * * *"  # Every 4 hours
```

## Schedule Formats

### Simple Format

```
--time HH:MM           # Daily at specific time
--day DAY --time HH:MM # Weekly on specific day
```

Examples:
- `--time 08:00` - Daily at 8 AM
- `--time 17:00` - Daily at 5 PM
- `--day monday --time 09:00` - Every Monday at 9 AM
- `--day friday --time 16:00` - Every Friday at 4 PM

### Cron Format (Advanced)

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-7, Sunday=0 or 7)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

Examples:
- `0 8 * * *` - Daily at 8 AM
- `0 9 * * 1` - Every Monday at 9 AM
- `0 */2 * * *` - Every 2 hours
- `0 9-17 * * 1-5` - Every hour, 9 AM - 5 PM, weekdays

## Task Configuration

Tasks are configured in `scheduler_config.json`:

```json
{
  "vault_path": "D:\\personal-AI-empy\\AI_Employee_Vault",
  "tasks": [
    {
      "name": "daily-briefing",
      "enabled": true,
      "schedule": "0 8 * * *",
      "command": "python",
      "args": ["watchers/generate_briefing.py"],
      "description": "Generate daily CEO briefing"
    },
    {
      "name": "gmail-check",
      "enabled": true,
      "schedule": "0 */2 * * *",
      "command": "python",
      "args": ["watchers/gmail_watcher.py"],
      "description": "Check Gmail every 2 hours"
    }
  ]
}
```

## Output Handling

Scheduled tasks can:

1. **Write to files** - Create markdown files in vault
2. **Send notifications** - Email/SMS alerts (if configured)
3. **Log results** - Write to Logs/ folder
4. **Update Dashboard** - Refresh Dashboard.md

## Logging

All scheduled tasks log to `Logs/scheduler.log`:

```
2026-03-13 08:00:01 - daily-briefing - STARTED
2026-03-13 08:00:15 - daily-briefing - COMPLETED
2026-03-13 10:00:01 - gmail-check - STARTED
2026-03-13 10:00:05 - gmail-check - COMPLETED (3 new emails)
```

## Error Handling

If a scheduled task fails:

1. Error is logged to `Logs/scheduler.log`
2. Error file created in `Logs/errors/`
3. Optional: Email notification sent
4. Task continues on next schedule

## Best Practices

| Practice | Description |
|----------|-------------|
| **Stagger times** | Don't run all tasks at same time |
| **Business hours** | Schedule notifications during work hours |
| **Weekend handling** | Different schedules for weekends |
| **Error alerts** | Get notified of failures |
| **Regular review** | Review task effectiveness monthly |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Task not running | Check scheduler service is running |
| Python not found | Use full path to python.exe |
| Permission denied | Run scheduler as administrator |
| Task fails silently | Check Logs/scheduler.log |

## Next Steps

After Task Scheduler is working:
1. Add email notifications for task failures
2. Configure different weekend schedules
3. Add task dependencies (task B runs after task A completes)
4. Implement task groups (enable/disable sets of tasks)

---

*Silver Tier Component - Part of Personal AI Employee Hackathon*
