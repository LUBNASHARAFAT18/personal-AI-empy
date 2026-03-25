# AI Employee - Bronze Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This is a **Personal AI Employee** implementation following the hackathon blueprint. The Bronze Tier provides the foundational layer for autonomous task management.

---

## 🎯 Bronze Tier Deliverables

- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [x] One working Watcher script (File System monitoring)
- [x] Claude Code reading/writing to the vault
- [x] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`

---

## 📁 Project Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time summary dashboard
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Drop files here for processing
├── Needs_Action/             # Items awaiting processing
├── Done/                     # Completed tasks
├── Plans/                    # AI-generated plans
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved actions
├── Rejected/                 # Rejected actions
├── Accounting/               # Financial records
├── Briefings/                # CEO briefings
├── Invoices/                 # Invoice files
├── Logs/                     # Activity logs
└── watchers/                 # Watcher scripts
    ├── base_watcher.py       # Abstract base class
    ├── filesystem_watcher.py # File system monitor
    └── requirements.txt      # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.13+ | Watcher scripts |
| Obsidian | v1.10.6+ | Knowledge base |
| Claude Code | Active subscription | AI reasoning engine |

### Installation

1. **Open the vault in Obsidian:**
   ```bash
   # Open Obsidian and select AI_Employee_Vault as your vault
   ```

2. **Verify Python version:**
   ```bash
   python --version
   # Should be 3.13 or higher
   ```

3. **Navigate to watchers directory:**
   ```bash
   cd AI_Employee_Vault/watchers
   ```

### Running the File System Watcher

The File System Watcher monitors the `Inbox` folder for new files and creates action files in `Needs_Action`.

```bash
# Start the watcher
python filesystem_watcher.py ../

# Or specify full path
python filesystem_watcher.py "D:\personal-AI-empy\AI_Employee_Vault"
```

**Expected output:**
```
=== AI Employee File System Watcher ===
Vault: D:\personal-AI-empy\AI_Employee_Vault
Monitoring: D:\personal-AI-empy\AI_Employee_Vault\Inbox
Output: D:\personal-AI-empy\AI_Employee_Vault\Needs_Action
Press Ctrl+C to stop
```

### Testing the Watcher

1. **Start the watcher** (leave it running)

2. **Drop a file in the Inbox:**
   - Copy any file (document, image, etc.) to the `Inbox` folder

3. **Check the output:**
   - A copy of the file appears in `Needs_Action`
   - A new `.md` file is created with metadata and action items

4. **Process with Claude Code:**
   ```bash
   # Navigate to vault and run Claude
   cd AI_Employee_Vault
   claude
   ```

5. **Prompt Claude:**
   ```
   Check the Needs_Action folder and process any pending items.
   Create a plan for each item and suggest next actions.
   ```

---

## 📖 How It Works

### 1. Perception (Watcher)
```
File dropped in Inbox → Watcher detects → Creates action file in Needs_Action
```

### 2. Reasoning (Claude Code)
```
Claude reads Needs_Action → Analyzes content → Creates Plan.md
```

### 3. Action (Human-in-the-Loop)
```
Claude suggests actions → Human approves → Task executed → Moved to Done
```

---

## 📝 Usage Examples

### Example 1: Process a Document

1. Drop `invoice_march.pdf` in `Inbox/`
2. Watcher creates `FILE_invoice_march_abc123_2026-03-06.md` in `Needs_Action/`
3. Run Claude Code:
   ```bash
   claude
   ```
4. Prompt:
   ```
   Review the new file in Needs_Action and categorize it.
   What actions should we take?
   ```

### Example 2: Batch Processing

Drop multiple files at once:
```bash
# Copy multiple files to Inbox
cp *.pdf Inbox/
cp *.docx Inbox/
```

The watcher will process each file and create corresponding action files.

---

## 🔧 Configuration

### Watcher Settings

Edit `filesystem_watcher.py` to customize:

```python
# Check interval (default: 30 seconds)
watcher = FileSystemWatcher(vault_path, check_interval=60)

# Priority keywords (automatically flags as high priority)
priority_keywords = ['urgent', 'asap', 'invoice', 'payment']
```

### Company Handbook Rules

Edit `Company_Handbook.md` to define:
- Auto-approval thresholds
- Communication guidelines
- Financial rules
- Restricted actions

---

## 📊 Dashboard

The `Dashboard.md` provides a real-time overview:

- Pending actions count
- Tasks completed today/week
- Financial summary
- Active projects
- Recent activity
- Alerts and notifications

**Update frequency:** Manually or via Claude Code after processing tasks.

---

## 🔐 Security Notes

### What's Safe
- ✅ File operations within vault
- ✅ Local processing (no cloud sync required)
- ✅ Human approval for all actions

### What to Avoid
- ❌ Never store credentials in vault files
- ❌ Never auto-execute financial transactions
- ❌ Never share vault contents publicly

### Best Practices
1. Use environment variables for API keys
2. Enable Obsidian vault encryption if syncing
3. Regular audit of `Logs/` folder
4. Review `Company_Handbook.md` monthly

---

## 🐛 Troubleshooting

### Watcher doesn't detect files
- Ensure watcher is running (`python filesystem_watcher.py`)
- Check file is in `Inbox/` folder (not subfolder)
- Verify file is not a `.md` file (already processed format)

### Action file not created
- Check watcher console for errors
- Verify `Needs_Action/` folder exists and is writable
- Ensure file hash isn't already processed (duplicate detection)

### Claude Code can't read vault
- Run Claude from within vault directory
- Check file permissions
- Verify Obsidian isn't locking files

---

## 📈 Next Steps (Silver Tier)

After mastering Bronze tier, upgrade to:

1. **Additional Watchers:**
   - Gmail Watcher (email monitoring)
   - WhatsApp Watcher (message monitoring)

2. **MCP Integration:**
   - Email MCP for sending replies
   - Browser MCP for web automation

3. **Automation:**
   - Scheduled tasks (cron/Task Scheduler)
   - Auto-posting to social media
   - Plan.md generation

---

## 📚 Resources

- [Hackathon Blueprint](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Claude Code Documentation](https://claude.com/product/claude-code)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Obsidian Help](https://help.obsidian.md/)

---

## 🤝 Contributing

This is a hackathon project. Feel free to:
- Fork and customize for your needs
- Add new watcher implementations
- Improve documentation
- Share lessons learned

---

**Version:** 0.1 (Bronze Tier)  
**Created:** 2026-03-06  
**License:** MIT (educational/hackathon use)
