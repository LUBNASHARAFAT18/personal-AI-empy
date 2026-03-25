# Cloud/Local Split Architecture for Platinum Tier
# Personal AI Employee - Production Deployment

"""
PLATINUM TIER ARCHITECTURE
===========================

┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD VM (24/7 Always-On)                    │
│                   (Oracle Cloud Free Tier)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLOUD AGENT (Draft-Only Mode)                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ Gmail      │ │ Email      │ │ Social     │                 │
│  │ Watcher    │ │ Triage     │ │ Scheduler  │                 │
│  │ (Read)     │ │ (Draft)    │ │ (Draft)    │                 │
│  └────────────┘ └────────────┘ └────────────┘                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CLOUD VAULT (Synced Subset)                             │   │
│  │  - /Inbox/                                               │   │
│  │  - /Needs_Action/                                        │   │
│  │  - /Plans/cloud/                                         │   │
│  │  - /Updates/ (Cloud → Local signals)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  NO SENSITIVE DATA: No tokens, sessions, banking creds         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↕ Git/Syncthing Sync
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE (Your Laptop)                  │
│                   (Human-in-the-Loop)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOCAL AGENT (Execution Mode)                                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ WhatsApp   │ │ Payments   │ │ Approval   │ │ Final      │  │
│  │ Watcher    │ │ & Banking  │ │ Handler    │ │ Send/Post  │  │
│  │ (Session)  │ │ (Creds)    │ │ (Human)    │ │ (Execute)  │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LOCAL VAULT (Full)                                      │   │
│  │  - All folders                                           │   │
│  │  - /Pending_Approval/ (Human reviews here)               │   │
│  │  - /Approved/ (Triggers execution)                       │   │
│  │  - /Done/                                                │   │
│  │  - /Signals/ (Cloud updates merged here)                 │   │
│  │  - Secrets (.env, tokens, sessions)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('platinum_architecture')


class AgentMode(Enum):
    CLOUD = "cloud"  # Draft-only mode
    LOCAL = "local"  # Execution mode


class PlatinumVault:
    """
    Manages vault sync between Cloud and Local with security rules.
    """

    def __init__(self, vault_path: str, mode: AgentMode):
        self.vault_path = Path(vault_path)
        self.mode = mode
        self.sync_config = self._load_sync_config()
        
        # Security: Never sync these
        self.NEVER_SYNC = [
            '.env',
            'token.json',
            'credentials.json',
            'whatsapp_session/',
            'banking_creds/',
            '*.key',
            '*.pem',
        ]
        
        # Cloud-only folders (Local owns these)
        self.LOCAL_ONLY_FOLDERS = [
            'Pending_Approval',
            'Approved',
            'Rejected',
            'Done',
            'Signals',
        ]

    def _load_sync_config(self) -> Dict:
        """Load sync configuration."""
        config_file = self.vault_path / 'platinum_sync_config.json'
        if config_file.exists():
            return json.loads(config_file.read_text())
        
        return {
            'sync_method': 'git',  # or 'syncthing'
            'sync_interval': 60,  # seconds
            'cloud_folders': ['Inbox', 'Needs_Action', 'Plans/cloud', 'Updates'],
            'local_folders': ['Pending_Approval', 'Approved', 'Done', 'Signals'],
        }

    def should_sync(self, file_path: Path) -> bool:
        """
        Check if file should be synced based on security rules.
        
        Returns:
            True if file can be synced, False if sensitive
        """
        file_str = str(file_path)
        
        # Check never-sync patterns
        for pattern in self.NEVER_SYNC:
            if pattern.endswith('/'):
                if pattern in file_str:
                    return False
            elif pattern.startswith('*'):
                if file_str.endswith(pattern[1:]):
                    return False
            else:
                if pattern in file_str:
                    return False
        
        # Cloud mode: Only sync cloud folders
        if self.mode == AgentMode.CLOUD:
            for folder in self.LOCAL_ONLY_FOLDERS:
                if folder in file_str:
                    return False
        
        return True

    def get_sync_folders(self) -> List[str]:
        """Get folders to sync based on mode."""
        if self.mode == AgentMode.CLOUD:
            return self.sync_config['cloud_folders']
        else:
            return self.sync_config['cloud_folders'] + self.sync_config['local_folders']


class ClaimByMoveRule:
    """
    Implements claim-by-move rule to prevent double-work.
    
    First agent to move item from /Needs_Action to /In_Progress/<agent>/ owns it.
    Other agents must ignore claimed items.
    """

    def __init__(self, vault_path: str, agent_name: str):
        self.vault_path = Path(vault_path)
        self.agent_name = agent_name
        self.in_progress_folder = self.vault_path / 'In_Progress' / agent_name
        self.in_progress_folder.mkdir(parents=True, exist_ok=True)

    def claim_task(self, task_file: Path) -> bool:
        """
        Claim a task by moving it to agent's In_Progress folder.
        
        Returns:
            True if successfully claimed, False if already claimed
        """
        if not task_file.exists():
            return False
        
        # Check if already in any In_Progress folder
        for agent_folder in (self.vault_path / 'In_Progress').iterdir():
            if agent_folder.is_dir():
                claimed_file = agent_folder / task_file.name
                if claimed_file.exists():
                    logger.info(f"Task {task_file.name} already claimed by {agent_folder.name}")
                    return False
        
        # Move to our In_Progress folder
        dest = self.in_progress_folder / task_file.name
        try:
            task_file.rename(dest)
            logger.info(f"Claimed task: {task_file.name} → {dest}")
            return True
        except Exception as e:
            logger.error(f"Failed to claim task: {e}")
            return False

    def release_task(self, task_file: Path, move_to_done: bool = False):
        """
        Release a task after completion.
        
        Args:
            task_file: Task file in In_Progress folder
            move_to_done: If True, move to Done folder
        """
        if move_to_done:
            done_folder = self.vault_path / 'Done'
            dest = done_folder / task_file.name
            task_file.rename(dest)
            logger.info(f"Task completed: {task_file.name} → {dest}")
        else:
            # Return to Needs_Action
            needs_action = self.vault_path / 'Needs_Action'
            dest = needs_action / task_file.name
            task_file.rename(dest)
            logger.info(f"Task released: {task_file.name} → {dest}")

    def get_claimed_tasks(self) -> List[Path]:
        """Get all tasks claimed by this agent."""
        return list(self.in_progress_folder.glob('*.md'))


class CloudLocalSignal:
    """
    Manages communication between Cloud and Local agents via file-based signals.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.updates_folder = self.vault_path / 'Updates'
        self.signals_folder = self.vault_path / 'Signals'
        
        for folder in [self.updates_folder, self.signals_folder]:
            folder.mkdir(parents=True, exist_ok=True)

    def send_cloud_to_local(self, signal_type: str, data: Dict) -> Path:
        """
        Cloud sends signal to Local agent.
        
        Args:
            signal_type: Type of signal (draft_ready, approval_needed, etc.)
            data: Signal data
        
        Returns:
            Path to signal file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"CLOUD_{signal_type}_{timestamp}.md"
        filepath = self.updates_folder / filename
        
        content = f'''---
type: cloud_signal
signal_type: {signal_type}
timestamp: {datetime.now().isoformat()}
direction: cloud_to_local
---

# Cloud → Local Signal

## Type
{signal_type}

## Data
{json.dumps(data, indent=2)}

## Instructions
Cloud agent has completed draft. Local agent should review and execute.
'''
        
        filepath.write_text(content)
        logger.info(f"Cloud signal sent: {filename}")
        return filepath

    def send_local_to_cloud(self, signal_type: str, data: Dict) -> Path:
        """
        Local sends signal to Cloud agent.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"LOCAL_{signal_type}_{timestamp}.md"
        filepath = self.signals_folder / filename
        
        content = f'''---
type: local_signal
signal_type: {signal_type}
timestamp: {datetime.now().isoformat()}
direction: local_to_cloud
---

# Local → Cloud Signal

## Type
{signal_type}

## Data
{json.dumps(data, indent=2)}
'''
        
        filepath.write_text(content)
        logger.info(f"Local signal sent: {filename}")
        return filepath

    def read_pending_signals(self, direction: str = 'cloud_to_local') -> List[Dict]:
        """
        Read pending signals.
        
        Args:
            direction: 'cloud_to_local' or 'local_to_cloud'
        
        Returns:
            List of signal data dictionaries
        """
        folder = self.updates_folder if direction == 'cloud_to_local' else self.signals_folder
        signals = []
        
        for signal_file in folder.glob('*.md'):
            content = signal_file.read_text()
            
            # Parse frontmatter
            import re
            data_match = re.search(r'## Data\n(.*?)\n\n##', content, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    signals.append(data)
                except:
                    continue
        
        return signals


# Example usage
if __name__ == '__main__':
    # Test vault sync rules
    vault = PlatinumVault('/tmp/test_vault', AgentMode.CLOUD)
    
    test_files = [
        Path('/tmp/test_vault/Inbox/email.md'),
        Path('/tmp/test_vault/token.json'),
        Path('/tmp/test_vault/Pending_Approval/approval.md'),
    ]
    
    for f in test_files:
        print(f"{f.name}: sync={vault.should_sync(f)}")
    
    # Test claim-by-move
    claimer = ClaimByMoveRule('/tmp/test_vault', 'cloud_agent')
    
    # Test signals
    signal = CloudLocalSignal('/tmp/test_vault')
    signal.send_cloud_to_local('draft_ready', {'email_id': 'abc123', 'draft': 'Reply draft...'})
