# Personal AI Employee - Project Context

## Project Overview

This is a **Personal AI Employee Hackathon** project focused on building autonomous AI agents ("Digital FTEs" - Full-Time Equivalents) that operate 24/7 to manage personal and business affairs. The project uses a **local-first, agent-driven, human-in-the-loop** architecture.

**Core Concept:** Transform AI from a chatbot into a proactive business partner that:
- Monitors communications (Gmail, WhatsApp, LinkedIn)
- Manages tasks and projects
- Handles accounting and bank transactions
- Posts to social media autonomously
- Generates executive briefings ("Monday Morning CEO Briefing")

## Architecture & Tech Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine with autonomous task completion |
| **Memory/GUI** | Obsidian (Markdown) | Dashboard, knowledge base, local data storage |
| **Senses** | Python Watcher Scripts | Monitor Gmail, WhatsApp, filesystems |
| **Hands** | MCP Servers | External actions (email, browser automation, payments) |
| **Persistence** | Ralph Wiggum Loop | Stop hook pattern for multi-step autonomous tasks |

## Key Features

### 1. Watcher Architecture
Lightweight Python scripts that continuously monitor inputs and create actionable `.md` files in `/Needs_Action` folders:
- **Gmail Watcher:** Monitors unread/important emails
- **WhatsApp Watcher:** Uses Playwright for WhatsApp Web automation
- **File System Watcher:** Monitors drop folders using `watchdog`

### 2. Human-in-the-Loop (HITL)
For sensitive actions (payments, sending messages), Claude writes approval request files to `/Pending_Approval` instead of acting directly. User moves file to `/Approved` to execute.

### 3. Ralph Wiggum Loop
A Stop hook pattern that keeps Claude working autonomously until tasks are complete by re-injecting prompts when Claude tries to exit prematurely.

### 4. Business Handover
Scheduled audits that generate "Monday Morning CEO Briefing" reports covering:
- Revenue tracking
- Completed tasks
- Bottlenecks
- Cost optimization suggestions (unused subscriptions)

## Project Structure

```
D:\personal-AI-empy\
├── .qwen/skills/               # Qwen agent skills
│   └── browsing-with-playwright/
│       ├── SKILL.md            # Skill documentation
│       ├── scripts/            # MCP server management scripts
│       └── references/         # Tool reference docs
├── .gitattributes              # Git text file normalization
├── skills-lock.json            # Skills version lock file
└── Personal AI Employee Hackathon...md  # Full hackathon blueprint
```

## Obsidian Vault Structure (To Be Created)

```
Vault/
├── Dashboard.md              # Real-time summary
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives & metrics
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring processing
├── In_Progress/<agent>/      # Claimed tasks (prevents double-work)
├── Pending_Approval/         # Awaiting user approval
├── Approved/                 # Approved actions (triggers execution)
├── Rejected/                 # Rejected actions
├── Done/                     # Completed tasks
├── Plans/                    # Generated plans (Plan.md)
├── Accounting/               # Bank transactions, Current_Month.md
└── Briefings/                # CEO briefings
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers |
| GitHub Desktop | Latest | Version control |

**Hardware:** Minimum 8GB RAM, 4-core CPU, 20GB free disk. Recommended: 16GB RAM, 8-core CPU, SSD.

### MCP Server Management (Playwright)

```bash
# Start browser automation server
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Stop server (closes browser first)
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh

# Verify server is running
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Typical Workflow

1. **Watcher detects change** → Creates `.md` file in `/Needs_Action`
2. **Claude reads** → Processes files, creates `Plan.md`
3. **Ralph Wiggum loop** → Keeps Claude working until complete
4. **Sensitive actions** → Written to `/Pending_Approval`
5. **User approval** → Move file to `/Approved`
6. **MCP execution** → Action performed via Model Context Protocol
7. **Task completion** → File moved to `/Done`

## Development Conventions

### File Naming
- Action files: `<TYPE>_<ID>_<DATE>.md` (e.g., `EMAIL_abc123_2026-01-07.md`)
- Approval files: `APPROVAL_REQUIRED_<Description>.md`
- Briefings: `<DATE>_<Day>_Briefing.md`

### Markdown Frontmatter
All actionable files use YAML frontmatter:
```yaml
---
type: email|payment|task|approval_request
from: sender@example.com
priority: high|medium|low
status: pending|approved|rejected|done
created: 2026-01-07T10:30:00Z
---
```

### Agent Skills
All AI functionality should be implemented as **Claude Agent Skills** (per hackathon requirements). Skills are stored in `.qwen/skills/` directory.

### Security Rules
- Secrets never sync between agents (`.env`, tokens, WhatsApp sessions, banking credentials)
- Cloud agents work in "draft-only" mode
- Local agents execute final "send/post" actions
- Vault sync includes only markdown/state files

## Achievement Tiers

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hrs | Obsidian vault, 1 Watcher, Claude reading/writing, basic folders |
| **Silver** | 20-30 hrs | 2+ Watchers, LinkedIn posting, Plan.md, 1 MCP server, HITL workflow |
| **Gold** | 40+ hrs | Full integration, Odoo accounting, social media integration, Ralph Wiggum loop |
| **Platinum** | 60+ hrs | 24/7 cloud deployment, Cloud/Local split, synced vault, production-ready |

## Key Commands

```bash
# Check Python version
python --version

# Check Node.js version
node --version

# Start Playwright MCP server
bash scripts/start-server.sh

# Run Ralph loop (autonomous task completion)
/ralph-loop "Process all files in /Needs_Action" --completion-promise "TASK_COMPLETE" --max-iterations 10
```

## Research Meetings

- **When:** Wednesdays at 10:00 PM PKT
- **Zoom:** https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1
- **YouTube:** https://www.youtube.com/@panaversity

## Resources

- [Claude Code Documentation](https://claude.com/product/claude-code)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Servers](https://github.com/anthropics/claude-code/tree/main/.claude/plugins)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [Playwright MCP Tools](.qwen/skills/browsing-with-playwright/references/playwright-tools.md)
