# 🤖 Personal AI Employee

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

[![Tier Status](https://img.shields.io/badge/Tier-Platinum-blue)](https://github.com/yourusername/personal-ai-employee)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/yourusername/personal-ai-employee)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://github.com/yourusername/personal-ai-employee)

---

## 🎯 Overview

Personal AI Employee ek **autonomous digital FTE (Full-Time Equivalent)** hai jo 24/7 operate karta hai aur aapke personal aur business affairs ko manage karta hai.

### **Key Features:**

- 📧 **Gmail Monitoring** - Auto-triage emails, draft replies
- 💬 **WhatsApp Integration** - Urgent message detection
- 📱 **Social Media Auto-Posting** - LinkedIn, Facebook, Instagram, Twitter
- 💰 **Accounting (Odoo)** - Invoice management, payment tracking
- 📊 **CEO Briefings** - Weekly business audits
- ✅ **Human-in-the-Loop** - Approval workflow for sensitive actions
- ☁️ **Cloud 24/7** - Always-on deployment (Oracle Cloud Free Tier)

---

## 🏆 Achievement Tiers

| Tier | Status | Features |
|------|--------|----------|
| **Bronze** | ✅ Complete | File Watcher, Basic Structure |
| **Silver** | ✅ Complete | Gmail, WhatsApp, LinkedIn, Plans, HITL, Scheduler |
| **Gold** | ✅ Complete | Odoo Accounting, Social Media, CEO Briefing, Audit |
| **Platinum** | ✅ Complete | Cloud 24/7, Cloud/Local Split, Health Monitoring |

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.12+
- Docker & Docker Compose
- Node.js v24+ (for MCP servers)
- Git

### **Installation**

```bash
# Clone repository
git clone https://github.com/yourusername/personal-ai-employee.git
cd personal-ai-employee

# Install Python dependencies
pip install -r AI_Employee_Vault/watchers/requirements.txt

# Start Docker (Odoo Accounting)
docker-compose up -d

# Verify
docker ps
```

### **Configure Gmail Watcher**

```bash
# 1. Download credentials.json from Google Cloud Console
# 2. Place in AI_Employee_Vault/credentials.json
# 3. Authenticate

cd AI_Employee_Vault/watchers
python gmail_watcher.py ../AI_Employee_Vault --authenticate
```

### **Start Watchers**

```bash
# File System Watcher
python watchers/filesystem_watcher.py AI_Employee_Vault

# Gmail Watcher
python watchers/gmail_watcher.py AI_Employee_Vault

# HITL Approval (background)
python watchers/hitl_approval.py AI_Employee_Vault --watch &
```

---

## 📁 Project Structure

```
personal-ai-employee/
├── .qwen/skills/               # Agent Skills (11 skills)
│   ├── gmail-watcher/
│   ├── whatsapp-watcher/
│   ├── linkedin-poster/
│   ├── ceo-briefing-generator/
│   └── ...
│
├── AI_Employee_Vault/          # Obsidian Vault
│   ├── Dashboard.md            # Real-time summary
│   ├── Business_Goals.md       # Objectives & metrics
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── watchers/               # Python watcher scripts
│   ├── Inbox/                  # Raw incoming items
│   ├── Needs_Action/           # Items requiring processing
│   ├── Pending_Approval/       # Awaiting approval
│   ├── Approved/               # Ready for execution
│   ├── Done/                   # Completed tasks
│   └── Briefings/              # CEO briefings
│
├── platinum/                   # Platinum Tier deployment
│   ├── deploy-to-oracle-cloud.sh
│   ├── cloud_local_architecture.py
│   └── health_monitor.py
│
├── odoo-mcp/                   # Odoo MCP Server
│   ├── Dockerfile
│   └── odoo_mcp_server.py
│
└── docker-compose.yml          # Odoo stack
```

---

## 🔒 Security

### **Never Commit These Files:**

```bash
.env                    # API keys
token.json              # OAuth tokens
credentials.json        # API credentials
whatsapp_session/       # WhatsApp session
banking_creds/          # Banking credentials
```

All sensitive files are in `.gitignore` - **automatically excluded from git**.

---

## ☁️ Cloud Deployment (Platinum Tier)

### **Deploy to Oracle Cloud Free Tier**

```bash
cd platinum
./deploy-to-oracle-cloud.sh
```

**Requirements:**
- Oracle Cloud account (free tier: 4 OCPU, 24GB RAM)
- OCI CLI installed
- SSH key pair

**Output:**
- VM instance created
- Public IP assigned
- Docker + Odoo auto-installed

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│         CLOUD VM (24/7)                 │
│  - Gmail Watcher (read/draft)          │
│  - Email Triage                         │
│  - Social Scheduler (draft)            │
│  - NO secrets                          │
└─────────────────────────────────────────┘
                ↕ Git Sync
┌─────────────────────────────────────────┐
│         LOCAL (Your Laptop)             │
│  - WhatsApp (session stored here)       │
│  - Payments (creds stored here)         │
│  - Human Approvals                      │
│  - Final Send/Post                      │
└─────────────────────────────────────────┘
```

---

## 🧪 Testing

### **Test File System Watcher**

```bash
# Drop a file in Inbox
echo "Test content" > AI_Employee_Vault/Inbox/test.txt

# Watcher creates action file
ls AI_Employee_Vault/Needs_Action/
```

### **Test CEO Briefing**

```bash
python AI_Employee_Vault/watchers/ceo_briefing.py AI_Employee_Vault
cat AI_Employee_Vault/Briefings/*_Briefing.md
```

### **Test Health Monitor**

```bash
python platinum/health_monitor.py AI_Employee_Vault --check
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PLATINUM_COMPLETE.md](AI_Employee_Vault/PLATINUM_COMPLETE.md) | Full implementation summary |
| [GOLD_TIER_COMPLETE.md](AI_Employee_Vault/GOLD_TIER_COMPLETE.md) | Gold tier details |
| [PLATINUM_TIER.md](AI_Employee_Vault/PLATINUM_TIER.md) | Platinum deployment guide |
| [TEST_REPORT.md](AI_Employee_Vault/TEST_REPORT.md) | Test results |

---

## 🎓 Agent Skills

All AI functionality implemented as **Claude Agent Skills**:

1. **gmail-watcher** - Monitor Gmail
2. **whatsapp-watcher** - Monitor WhatsApp
3. **linkedin-poster** - LinkedIn auto-posting
4. **plan-generator** - Task planning
5. **hitl-approval-workflow** - Approval workflow
6. **task-scheduler** - Task scheduling
7. **ceo-briefing-generator** - Weekly briefings
8. **facebook-instagram-integration** - Meta platforms
9. **twitter-x-integration** - Twitter integration
10. **ralph-wiggum-loop** - Autonomous tasks
11. **browsing-with-playwright** - Browser automation

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 📞 Support

- **Hackathon Meetings:** Wednesdays at 10:00 PM PKT
- **Zoom:** [Meeting Link](https://us06web.zoom.us/j/87188707642)
- **YouTube:** [Panaversity](https://www.youtube.com/@panaversity)

---

## 🏆 Acknowledgments

- **Claude Code** - Reasoning engine
- **Obsidian** - Knowledge base & dashboard
- **Odoo** - Accounting system
- **Meta Graph API** - Facebook/Instagram
- **Twitter API** - Twitter integration
- **Playwright** - Browser automation

---

*Built with ❤️ for the Personal AI Employee Hackathon 2026*
