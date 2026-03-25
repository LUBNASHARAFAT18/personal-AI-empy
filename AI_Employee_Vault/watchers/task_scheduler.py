"""
Task Scheduler - Install and manage scheduled tasks for AI Employee.

Supports:
- Windows Task Scheduler (schtasks)
- Linux/Mac cron (crontab)
- Predefined tasks (daily briefing, weekly audit, etc.)
- Custom task scheduling

Usage:
    python task_scheduler.py /path/to/vault --install --task daily-briefing --time 08:00
    python task_scheduler.py /path/to/vault --list
    python task_scheduler.py /path/to/vault --remove --task daily-briefing
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# Predefined task definitions
PREDEFINED_TASKS = {
    'daily-briefing': {
        'description': 'Generate daily CEO briefing',
        'script': 'watchers/generate_briefing.py',
        'default_time': '08:00',
        'default_day': None,
    },
    'weekly-audit': {
        'description': 'Weekly business audit and summary',
        'script': 'watchers/weekly_audit.py',
        'default_time': '09:00',
        'default_day': 'monday',
    },
    'gmail-check': {
        'description': 'Check Gmail for new messages',
        'script': 'watchers/gmail_watcher.py',
        'default_time': None,  # Runs continuously
        'default_day': None,
    },
    'whatsapp-check': {
        'description': 'Check WhatsApp for urgent messages',
        'script': 'watchers/whatsapp_watcher.py',
        'default_time': None,  # Runs continuously
        'default_day': None,
    },
    'linkedin-post': {
        'description': 'Post scheduled LinkedIn updates',
        'script': 'watchers/linkedin_poster.py',
        'default_time': '09:00',
        'default_day': None,
    },
    'approval-check': {
        'description': 'Check and execute approved actions',
        'script': 'watchers/hitl_approval.py',
        'default_time': None,  # Runs continuously
        'default_day': None,
    },
}


class TaskScheduler:
    """
    Manage scheduled tasks for AI Employee.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the task scheduler.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.config_file = self.vault_path / 'scheduler_config.json'
        self.logs_folder = self.vault_path / 'Logs'
        self.watchers_folder = self.vault_path / 'watchers'
        
        # Ensure folders exist
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
        
        # Detect OS
        self.is_windows = sys.platform.startswith('win')

    def _load_config(self) -> Dict:
        """Load scheduler configuration."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding='utf-8'))
            except:
                pass
        
        # Default config
        return {
            'vault_path': str(self.vault_path),
            'python_path': sys.executable,
            'tasks': []
        }

    def _save_config(self):
        """Save scheduler configuration."""
        self.config_file.write_text(json.dumps(self.config, indent=2), encoding='utf-8')

    def install_task(self, task_name: str, time: Optional[str] = None, 
                     day: Optional[str] = None, schedule: Optional[str] = None,
                     custom_script: Optional[str] = None) -> bool:
        """
        Install a scheduled task.

        Args:
            task_name: Name of task (predefined or 'custom')
            time: Time to run (HH:MM format)
            day: Day of week (monday, tuesday, etc.)
            schedule: Cron schedule (advanced)
            custom_script: Path to custom script (for custom tasks)

        Returns:
            True if installation successful
        """
        # Get task definition
        if task_name == 'custom':
            if not custom_script:
                print("Error: --script required for custom tasks")
                return False
            
            task_def = {
                'name': f'custom-{Path(custom_script).stem}',
                'description': 'Custom scheduled task',
                'script': custom_script,
            }
        elif task_name in PREDEFINED_TASKS:
            task_def = PREDEFINED_TASKS[task_name].copy()
            task_def['name'] = task_name
        else:
            print(f"Error: Unknown task '{task_name}'")
            print(f"Available tasks: {', '.join(PREDEFINED_TASKS.keys())}")
            return False
        
        # Determine schedule
        if schedule:
            cron_schedule = schedule
        elif day and time:
            # Weekly schedule
            day_num = self._day_to_num(day)
            cron_schedule = f"0 {time} * * {day_num}"
        elif time:
            # Daily schedule
            cron_schedule = f"0 {time} * * *"
        else:
            # Use default
            if task_def.get('default_day') and task_def.get('default_time'):
                day_num = self._day_to_num(task_def['default_day'])
                cron_schedule = f"0 {task_def['default_time']} * * {day_num}"
            elif task_def.get('default_time'):
                cron_schedule = f"0 {task_def['default_time']} * * *"
            else:
                print("Error: No schedule specified and task has no default")
                return False
        
        # Build task config
        task_config = {
            'name': task_def['name'],
            'description': task_def.get('description', ''),
            'enabled': True,
            'schedule': cron_schedule,
            'command': self.config.get('python_path', sys.executable),
            'args': [str(Path(self.watchers_folder) / task_def['script'])],
        }
        
        # Add to config
        self.config['tasks'].append(task_config)
        self._save_config()
        
        # Install in OS scheduler
        if self.is_windows:
            return self._install_windows_task(task_config)
        else:
            return self._install_cron_task(task_config)

    def _day_to_num(self, day: str) -> int:
        """Convert day name to cron day number."""
        days = {
            'sunday': 0, 'sun': 0,
            'monday': 1, 'mon': 1,
            'tuesday': 2, 'tue': 2,
            'wednesday': 3, 'wed': 3,
            'thursday': 4, 'thu': 4,
            'friday': 5, 'fri': 5,
            'saturday': 6, 'sat': 6,
        }
        return days.get(day.lower(), 1)

    def _install_windows_task(self, task_config: Dict) -> bool:
        """Install task in Windows Task Scheduler."""
        task_name = f"AI_Employee_{task_config['name']}"
        
        # Build command
        command = task_config['command']
        args = ' '.join(f'"{arg}"' for arg in task_config['args'])
        full_command = f'{command} {args}'
        
        # Parse schedule for schtasks
        schedule = task_config['schedule']
        parts = schedule.split()
        
        if len(parts) == 5:
            minute, hour, day_of_month, month, day_of_week = parts
            
            # Build schtasks command
            if day_of_week == '*':
                # Daily task
                schtasks_cmd = [
                    'schtasks', '/Create',
                    '/TN', task_name,
                    '/TR', full_command,
                    '/SC', 'DAILY',
                    '/ST', f"{hour.zfill(2)}:{minute.zfill(2)}",
                    '/F'  # Force overwrite if exists
                ]
            else:
                # Weekly task
                schtasks_cmd = [
                    'schtasks', '/Create',
                    '/TN', task_name,
                    '/TR', full_command,
                    '/SC', 'WEEKLY',
                    '/D', self._num_to_day(day_of_week),
                    '/ST', f"{hour.zfill(2)}:{minute.zfill(2)}",
                    '/F'
                ]
            
            try:
                result = subprocess.run(schtasks_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[OK] Task installed: {task_name}")
                    print(f"  Schedule: {schedule}")
                    return True
                else:
                    print(f"[FAIL] Failed to install task: {result.stderr}")
                    return False
            except Exception as e:
                print(f"[FAIL] Error: {e}")
                return False
        
        print(f"Error: Could not parse schedule: {schedule}")
        return False

    def _num_to_day(self, num: str) -> str:
        """Convert cron day number to Windows day name."""
        days = {
            '0': 'SUN', '1': 'MON', '2': 'TUE', '3': 'WED',
            '4': 'THU', '5': 'FRI', '6': 'SAT', '7': 'SAT'
        }
        return days.get(num, 'MON')

    def _install_cron_task(self, task_config: Dict) -> bool:
        """Install task in cron."""
        task_name = f"AI_Employee_{task_config['name']}"
        
        # Build command
        command = task_config['command']
        args = ' '.join(f'"{arg}"' for arg in task_config['args'])
        full_command = f'{command} {args}'
        
        # Get current crontab
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ''
        except:
            current_crontab = ''
        
        # Check if task already exists
        lines = current_crontab.split('\n')
        new_lines = [l for l in lines if task_name not in l]
        
        # Add new task
        cron_entry = f"{task_config['schedule']} {full_command} # {task_name}"
        new_lines.append(cron_entry)
        
        # Install new crontab
        new_crontab = '\n'.join(new_lines)
        
        try:
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            print(f"[OK] Task installed: {task_name}")
            print(f"  Schedule: {task_config['schedule']}")
            return True
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            return False

    def list_tasks(self):
        """List all installed tasks."""
        print("\n=== Installed AI Employee Tasks ===\n")
        
        # From config
        for task in self.config.get('tasks', []):
            status = "[OK]" if task.get('enabled', True) else "[FAIL]"
            print(f"{status} {task['name']}")
            print(f"   Description: {task.get('description', 'N/A')}")
            print(f"   Schedule: {task.get('schedule', 'N/A')}")
            print(f"   Command: {task.get('command', '')} {' '.join(task.get('args', []))}")
            print()
        
        # From OS scheduler
        if self.is_windows:
            print("=== Windows Task Scheduler ===\n")
            try:
                result = subprocess.run(
                    ['schtasks', '/Query', '/FO', 'TABLE', '/TN', 'AI_Employee_*'],
                    capture_output=True, text=True
                )
                print(result.stdout)
            except:
                print("Could not query Windows Task Scheduler")
        else:
            print("=== Cron Tasks ===\n")
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'AI_Employee' in line:
                        print(line)
            except:
                print("No cron tasks found")

    def remove_task(self, task_name: str) -> bool:
        """Remove a scheduled task."""
        # Remove from config
        self.config['tasks'] = [t for t in self.config['tasks'] if t['name'] != task_name]
        self._save_config()
        
        # Remove from OS scheduler
        full_task_name = f"AI_Employee_{task_name}"
        
        if self.is_windows:
            try:
                subprocess.run(['schtasks', '/Delete', '/TN', full_task_name, '/F'],
                             capture_output=True)
                print(f"[OK] Task removed: {full_task_name}")
                return True
            except Exception as e:
                print(f"[FAIL] Error: {e}")
                return False
        else:
            # Remove from crontab
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                lines = [l for l in result.stdout.split('\n') if full_task_name not in l]
                new_crontab = '\n'.join(lines)
                
                process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
                process.communicate(input=new_crontab)
                print(f"[OK] Task removed: {full_task_name}")
                return True
            except Exception as e:
                print(f"[FAIL] Error: {e}")
                return False

    def show_crontab(self):
        """Show crontab entry for manual installation."""
        if self.is_windows:
            print("This command is for Linux/Mac only (uses cron)")
            return
        
        print("# AI Employee Tasks - Crontab Entries")
        print("# Copy these lines to your crontab (crontab -e)")
        print()
        
        for task in self.config.get('tasks', []):
            command = task.get('command', 'python')
            args = ' '.join(f'"{arg}"' for arg in task.get('args', []))
            schedule = task.get('schedule', '')
            name = task.get('name', 'unknown')
            
            print(f"{schedule} {command} {args} # AI_Employee_{name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Task Scheduler for AI Employee')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--install', action='store_true', help='Install a scheduled task')
    parser.add_argument('--task', type=str, help='Task name (daily-briefing, weekly-audit, etc.)')
    parser.add_argument('--time', type=str, help='Time to run (HH:MM format)')
    parser.add_argument('--day', type=str, help='Day of week (monday, tuesday, etc.)')
    parser.add_argument('--schedule', type=str, help='Cron schedule (advanced)')
    parser.add_argument('--script', type=str, help='Custom script path (for custom tasks)')
    parser.add_argument('--list', action='store_true', help='List installed tasks')
    parser.add_argument('--remove', action='store_true', help='Remove a task')
    parser.add_argument('--show-crontab', action='store_true', help='Show crontab entries')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault_path:
        vault_path = Path(args.vault_path).resolve()
    else:
        vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
        vault_path = vault_path.resolve()
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    scheduler = TaskScheduler(str(vault_path))
    
    if args.install:
        if not args.task:
            print("Error: --task is required")
            print(f"Available tasks: {', '.join(PREDEFINED_TASKS.keys())}")
            sys.exit(1)
        
        success = scheduler.install_task(
            task_name=args.task,
            time=args.time,
            day=args.day,
            schedule=args.schedule,
            custom_script=args.script
        )
        
        if not success:
            sys.exit(1)
    
    elif args.list:
        scheduler.list_tasks()
    
    elif args.remove:
        if not args.task:
            print("Error: --task is required")
            sys.exit(1)
        
        scheduler.remove_task(args.task)
    
    elif args.show_crontab:
        scheduler.show_crontab()
    
    else:
        parser.print_help()
        print("\nAvailable tasks:")
        for name, info in PREDEFINED_TASKS.items():
            default = info.get('default_time') or 'continuous'
            print(f"  {name}: {info.get('description', '')} (default: {default})")


if __name__ == '__main__':
    main()
