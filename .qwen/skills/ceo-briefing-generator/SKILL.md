---
name: ceo-briefing-generator
description: |
  Generates comprehensive weekly CEO briefings with business audits,
  revenue tracking, task summaries, bottlenecks analysis, and proactive
  suggestions. Runs weekly (Monday morning) to provide executive insights.
---

# CEO Briefing Generator

Automatically generates "Monday Morning CEO Briefing" reports.

## Overview

The CEO Briefing is a comprehensive weekly audit that transforms raw data into actionable executive insights.

## Features

- **Revenue Tracking**: Weekly/Monthly revenue analysis
- **Task Summary**: Completed tasks breakdown
- **Bottleneck Analysis**: Identify delays and blockers
- **Subscription Audit**: Unused/expensive subscriptions
- **Upcoming Deadlines**: Project timeline review
- **Proactive Suggestions**: AI-generated recommendations

## Usage

```bash
# Generate weekly briefing
python ceo_briefing.py AI_Employee_Vault

# Generate with custom date range
python ceo_briefing.py AI_Employee_Vault --start-date 2026-03-01 --end-date 2026-03-07

# Generate and save to specific folder
python ceo_briefing.py AI_Employee_Vault --output-folder Briefings
```

## Output Format

Generates markdown file in `Briefings/` folder:

```markdown
# Monday Morning CEO Briefing
**Period:** March 1-7, 2026

## Executive Summary
Strong week with revenue ahead of target. One bottleneck identified.

## Revenue
- **This Week:** $2,450
- **MTD:** $4,500 (45% of $10,000 target)
- **Trend:** On track

## Completed Tasks
- [x] Client A invoice sent and paid
- [x] Project Alpha milestone 2 delivered
- [x] Weekly social media posts scheduled

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |

## Proactive Suggestions

### Cost Optimization
- **Notion**: No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription? Move to Pending_Approval

### Upcoming Deadlines
- Project Alpha final delivery: Jan 15 (9 days)
- Quarterly tax prep: Jan 31 (25 days)
```

## Scheduled Execution

```bash
# Schedule for every Monday at 8 AM
python task_scheduler.py AI_Employee_Vault --install --task weekly-briefing --day monday --time 08:00
```

---

*Gold Tier Component - Personal AI Employee Hackathon*
