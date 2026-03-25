"""
Comprehensive Audit Logging System for AI Employee.

Logs all actions, decisions, and state changes for compliance and debugging.
Implements structured JSON logging with rotation and search capabilities.

Usage:
    python audit_logger.py AI_Employee_Vault --log-action --type email_send --result success
    python audit_logger.py AI_Employee_Vault --search --query "payment"
    python audit_logger.py AI_Employee_Vault --daily-report --date 2026-03-23
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class AuditLogger:
    """
    Comprehensive audit logging for AI Employee.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the audit logger.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs' / 'audit'
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Current log file (daily rotation)
        self.current_log_file = self._get_today_log_file()
        
        # Log buffer for batch writing
        self.log_buffer = []

    def _get_today_log_file(self) -> Path:
        """Get today's log file path."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return self.logs_folder / f'audit_{date_str}.json'

    def log(self, action_type: str, actor: str, target: str,
            result: str = 'success', parameters: Optional[Dict] = None,
            approval_status: Optional[str] = None, approved_by: Optional[str] = None,
            error: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log an action.

        Args:
            action_type: Type of action (email_send, payment, post, etc.)
            actor: Who performed the action (claude_code, human, watcher)
            target: Target of action (email address, file, etc.)
            result: success, failure, skipped
            parameters: Action parameters
            approval_status: pending, approved, rejected, not_required
            approved_by: Person who approved (if applicable)
            error: Error message (if failed)
            metadata: Additional metadata
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': actor,
            'target': target,
            'result': result,
            'parameters': parameters or {},
            'approval_status': approval_status,
            'approved_by': approved_by,
            'error': error,
            'metadata': metadata or {}
        }
        
        # Add to buffer
        self.log_buffer.append(log_entry)
        
        # Write buffer to file
        self._flush_buffer()
        
        return log_entry

    def _flush_buffer(self):
        """Write log buffer to file."""
        if not self.log_buffer:
            return
        
        log_file = self._get_today_log_file()
        
        # Load existing logs
        existing_logs = []
        if log_file.exists():
            try:
                existing_logs = json.loads(log_file.read_text(encoding='utf-8'))
            except:
                existing_logs = []
        
        # Append new logs
        existing_logs.extend(self.log_buffer)
        
        # Write back
        log_file.write_text(json.dumps(existing_logs, indent=2), encoding='utf-8')
        
        # Clear buffer
        self.log_buffer = []

    def search(self, query: str, date_from: Optional[datetime] = None,
              date_to: Optional[datetime] = None,
              action_type: Optional[str] = None,
              actor: Optional[str] = None) -> List[Dict]:
        """
        Search audit logs.

        Args:
            query: Text search query
            date_from: Start date
            date_to: End date
            action_type: Filter by action type
            actor: Filter by actor

        Returns:
            List of matching log entries
        """
        results = []
        
        # Determine date range
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        # Search all log files in range
        current_date = date_from
        while current_date <= date_to:
            log_file = self.logs_folder / f'audit_{current_date.strftime("%Y-%m-%d")}.json'
            
            if log_file.exists():
                try:
                    logs = json.loads(log_file.read_text(encoding='utf-8'))
                    
                    for entry in logs:
                        # Apply filters
                        if action_type and entry.get('action_type') != action_type:
                            continue
                        if actor and entry.get('actor') != actor:
                            continue
                        
                        # Text search
                        if query:
                            entry_text = json.dumps(entry).lower()
                            if query.lower() not in entry_text:
                                continue
                        
                        results.append(entry)
                
                except Exception as e:
                    continue
            
            current_date += timedelta(days=1)
        
        return results

    def get_daily_report(self, date: datetime) -> Dict:
        """
        Generate daily audit report.

        Args:
            date: Report date

        Returns:
            Daily report dictionary
        """
        log_file = self.logs_folder / f'audit_{date.strftime("%Y-%m-%d")}.json'
        
        if not log_file.exists():
            return {'date': date.strftime('%Y-%m-%d'), 'total_actions': 0}
        
        try:
            logs = json.loads(log_file.read_text(encoding='utf-8'))
        except:
            return {'date': date.strftime('%Y-%m-%d'), 'total_actions': 0}
        
        # Aggregate statistics
        report = {
            'date': date.strftime('%Y-%m-%d'),
            'total_actions': len(logs),
            'by_result': defaultdict(int),
            'by_action_type': defaultdict(int),
            'by_actor': defaultdict(int),
            'by_approval_status': defaultdict(int),
            'errors': [],
            'success_rate': 0.0
        }
        
        for entry in logs:
            report['by_result'][entry.get('result', 'unknown')] += 1
            report['by_action_type'][entry.get('action_type', 'unknown')] += 1
            report['by_actor'][entry.get('actor', 'unknown')] += 1
            
            approval = entry.get('approval_status', 'not_recorded')
            report['by_approval_status'][approval] += 1
            
            if entry.get('result') == 'failure':
                report['errors'].append({
                    'timestamp': entry.get('timestamp'),
                    'action_type': entry.get('action_type'),
                    'error': entry.get('error')
                })
        
        # Calculate success rate
        total = report['total_actions']
        success = report['by_result'].get('success', 0)
        report['success_rate'] = (success / total * 100) if total > 0 else 0
        
        # Convert defaultdicts to regular dicts
        report['by_result'] = dict(report['by_result'])
        report['by_action_type'] = dict(report['by_action_type'])
        report['by_actor'] = dict(report['by_actor'])
        report['by_approval_status'] = dict(report['by_approval_status'])
        
        return report

    def get_compliance_report(self, date_from: datetime,
                             date_to: datetime) -> Dict:
        """
        Generate compliance report for date range.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Compliance report dictionary
        """
        report = {
            'period': {
                'from': date_from.strftime('%Y-%m-%d'),
                'to': date_to.strftime('%Y-%m-%d')
            },
            'total_actions': 0,
            'actions_requiring_approval': 0,
            'actions_with_approval': 0,
            'approval_compliance_rate': 0.0,
            'total_errors': 0,
            'error_rate': 0.0,
            'by_day': []
        }
        
        # Get daily reports
        current_date = date_from
        while current_date <= date_to:
            daily = self.get_daily_report(current_date)
            report['by_day'].append(daily)
            report['total_actions'] += daily.get('total_actions', 0)
            report['total_errors'] += len(daily.get('errors', []))
            
            # Count approval-related actions
            approval_stats = daily.get('by_approval_status', {})
            report['actions_requiring_approval'] += \
                approval_stats.get('pending', 0) + \
                approval_stats.get('approved', 0) + \
                approval_stats.get('rejected', 0)
            
            report['actions_with_approval'] += \
                approval_stats.get('approved', 0)
            
            current_date += timedelta(days=1)
        
        # Calculate rates
        if report['actions_requiring_approval'] > 0:
            report['approval_compliance_rate'] = \
                (report['actions_with_approval'] / report['actions_requiring_approval'] * 100)
        
        if report['total_actions'] > 0:
            report['error_rate'] = (report['total_errors'] / report['total_actions'] * 100)
        
        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Audit Logger')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--log-action', action='store_true', help='Log an action')
    parser.add_argument('--type', type=str, help='Action type')
    parser.add_argument('--actor', type=str, help='Actor (who performed action)')
    parser.add_argument('--target', type=str, help='Action target')
    parser.add_argument('--result', type=str, default='success', help='Result')
    parser.add_argument('--search', action='store_true', help='Search logs')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--daily-report', action='store_true', help='Generate daily report')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD)')
    parser.add_argument('--compliance-report', action='store_true', help='Compliance report')
    parser.add_argument('--date-from', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-to', type=str, help='End date (YYYY-MM-DD)')
    
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
    
    logger = AuditLogger(str(vault_path))
    
    if args.log_action:
        if not all([args.type, args.actor, args.target]):
            print("Error: --type, --actor, and --target required for logging")
            sys.exit(1)
        
        entry = logger.log(
            action_type=args.type,
            actor=args.actor,
            target=args.target,
            result=args.result
        )
        print(f"[OK] Logged action: {entry['timestamp']}")
    
    elif args.search:
        results = logger.search(args.query or '')
        print(f"\n=== Search Results ({len(results)} matches) ===\n")
        for entry in results[:20]:  # Show first 20
            print(f"{entry['timestamp']} - {entry['action_type']} - {entry['result']}")
            print(f"  Actor: {entry['actor']}, Target: {entry['target']}")
            print()
    
    elif args.daily_report:
        if not args.date:
            date = datetime.now()
        else:
            date = datetime.strptime(args.date, '%Y-%m-%d')
        
        report = logger.get_daily_report(date)
        
        print(f"\n=== Daily Audit Report: {report['date']} ===\n")
        print(f"Total Actions: {report['total_actions']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"\nBy Action Type:")
        for action_type, count in report.get('by_action_type', {}).items():
            print(f"  {action_type}: {count}")
        print(f"\nBy Result:")
        for result, count in report.get('by_result', {}).items():
            print(f"  {result}: {count}")
        if report.get('errors'):
            print(f"\nErrors ({len(report['errors'])}):")
            for error in report['errors'][:5]:
                print(f"  {error['timestamp']} - {error['action_type']}: {error['error']}")
    
    elif args.compliance_report:
        if not args.date_from or not args.date_to:
            print("Error: --date-from and --date-to required")
            sys.exit(1)
        
        date_from = datetime.strptime(args.date_from, '%Y-%m-%d')
        date_to = datetime.strptime(args.date_to, '%Y-%m-%d')
        
        report = logger.get_compliance_report(date_from, date_to)
        
        print(f"\n=== Compliance Report: {report['period']['from']} to {report['period']['to']} ===\n")
        print(f"Total Actions: {report['total_actions']}")
        print(f"Approval Compliance Rate: {report['approval_compliance_rate']:.1f}%")
        print(f"Error Rate: {report['error_rate']:.1f}%")
        print(f"Total Errors: {report['total_errors']}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
