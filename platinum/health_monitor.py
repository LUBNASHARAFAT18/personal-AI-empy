# Health Monitoring System for Platinum Tier
# Personal AI Employee - Production 24/7 Monitoring

"""
HEALTH MONITORING SYSTEM
=========================

Monitors all components and sends alerts on failures:
- Container health (Docker)
- Watcher processes
- API connectivity
- Vault sync status
- Resource usage (CPU, Memory, Disk)
"""

import os
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('health_monitor')


class HealthMonitor:
    """
    Comprehensive health monitoring for AI Employee.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs' / 'health'
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Health check configuration
        self.check_interval = 60  # seconds
        self.alert_threshold = 3  # consecutive failures before alert
        
        # Failure counters
        self.failure_counts = {
            'docker': 0,
            'watchers': 0,
            'odoo': 0,
            'vault_sync': 0,
        }
        
        # Load alert config
        self.alert_config = self._load_alert_config()

    def _load_alert_config(self) -> Dict:
        """Load alert configuration."""
        config_file = self.vault_path / 'platinum_alert_config.json'
        if config_file.exists():
            return json.loads(config_file.read_text())
        
        return {
            'email_alerts': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'alert_email': 'admin@example.com',
            'slack_webhook': None,
        }

    def check_docker_containers(self) -> Dict:
        """
        Check Docker container health.
        
        Returns:
            Container status dictionary
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}:{{.Status}}'],
                capture_output=True,
                text=True
            )
            
            containers = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    name, status = line.split(':', 1)
                    containers[name] = {
                        'status': 'healthy' if 'healthy' in status or 'Up' in status else 'unhealthy',
                        'details': status
                    }
            
            # Check required containers
            required = ['ai_employee_odoo', 'ai_employee_odoo_db', 'ai_employee_odoo_mcp']
            for container in required:
                if container not in containers:
                    containers[container] = {'status': 'not_running', 'details': 'Container not found'}
            
            return containers
            
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            return {'error': str(e)}

    def check_watcher_processes(self) -> List[Dict]:
        """
        Check watcher processes are running.
        
        Returns:
            List of watcher status dictionaries
        """
        watchers = [
            'filesystem_watcher.py',
            'gmail_watcher.py',
            'whatsapp_watcher.py',
            'hitl_approval.py',
            'ceo_briefing.py',
        ]
        
        status = []
        for watcher in watchers:
            try:
                # Check if process is running
                result = subprocess.run(
                    ['pgrep', '-f', watcher],
                    capture_output=True,
                    text=True
                )
                
                is_running = result.returncode == 0
                status.append({
                    'name': watcher,
                    'status': 'running' if is_running else 'stopped',
                    'pid': result.stdout.strip() if is_running else None
                })
                
            except Exception as e:
                status.append({
                    'name': watcher,
                    'status': 'error',
                    'error': str(e)
                })
        
        return status

    def check_odoo_connectivity(self) -> bool:
        """
        Check Odoo API connectivity.
        
        Returns:
            True if Odoo is reachable
        """
        try:
            import requests
            response = requests.get('http://localhost:8809/health', timeout=5)
            return response.status_code == 200
        except:
            return False

    def check_vault_sync(self) -> Dict:
        """
        Check vault sync status.
        
        Returns:
            Sync status dictionary
        """
        # Check if git repo exists and is synced
        git_dir = self.vault_path / '.git'
        
        if not git_dir.exists():
            return {'status': 'no_git', 'message': 'Not a git repository'}
        
        try:
            # Check git status
            result = subprocess.run(
                ['git', '-C', str(self.vault_path), 'status', '--porcelain'],
                capture_output=True,
                text=True
            )
            
            uncommitted = len(result.stdout.strip()) > 0
            
            return {
                'status': 'synced' if not uncommitted else 'has_changes',
                'uncommitted_changes': uncommitted,
                'last_sync': self._get_last_sync_time()
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _get_last_sync_time(self) -> Optional[str]:
        """Get last git sync time."""
        try:
            result = subprocess.run(
                ['git', '-C', str(self.vault_path), 'log', '-1', '--format=%ci'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return None

    def check_resource_usage(self) -> Dict:
        """
        Check system resource usage.
        
        Returns:
            Resource usage dictionary
        """
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
            }
            
        except ImportError:
            return {'error': 'psutil not installed'}
        except Exception as e:
            return {'error': str(e)}

    def run_health_check(self) -> Dict:
        """
        Run complete health check.
        
        Returns:
            Complete health status dictionary
        """
        health = {
            'timestamp': datetime.now().isoformat(),
            'containers': self.check_docker_containers(),
            'watchers': self.check_watcher_processes(),
            'odoo': {
                'status': 'healthy' if self.check_odoo_connectivity() else 'unhealthy'
            },
            'vault_sync': self.check_vault_sync(),
            'resources': self.check_resource_usage(),
        }
        
        # Determine overall health
        overall_health = 'healthy'
        
        # Check containers
        for container, status in health['containers'].items():
            if status.get('status') != 'healthy':
                overall_health = 'degraded'
                self.failure_counts['docker'] += 1
            else:
                self.failure_counts['docker'] = 0
        
        # Check Odoo
        if health['odoo']['status'] != 'healthy':
            overall_health = 'degraded'
            self.failure_counts['odoo'] += 1
        else:
            self.failure_counts['odoo'] = 0
        
        # Check resources
        resources = health['resources']
        if resources.get('cpu_percent', 0) > 90 or resources.get('memory_percent', 0) > 90:
            overall_health = 'critical'
        
        health['overall_status'] = overall_health
        
        # Save health log
        self._save_health_log(health)
        
        # Send alerts if needed
        self._check_and_send_alerts(health)
        
        return health

    def _save_health_log(self, health: Dict):
        """Save health check to log file."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_folder / f'health_{date_str}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(health)
        
        # Keep only last 100 entries
        logs = logs[-100:]
        
        log_file.write_text(json.dumps(logs, indent=2))

    def _check_and_send_alerts(self, health: Dict):
        """Send alerts if failure threshold exceeded."""
        alerts = []
        
        for component, count in self.failure_counts.items():
            if count >= self.alert_threshold:
                alerts.append({
                    'component': component,
                    'message': f'{component} failed {count} consecutive times',
                    'severity': 'critical' if count >= 5 else 'warning'
                })
        
        if alerts:
            self._send_alert(alerts, health)

    def _send_alert(self, alerts: List[Dict], health: Dict):
        """Send alert via email/Slack."""
        subject = f"🚨 AI Employee Alert - {health['overall_status'].upper()}"
        
        body = f"""
AI Employee Health Alert

Time: {health['timestamp']}
Overall Status: {health['overall_status']}

Alerts:
"""
        
        for alert in alerts:
            body += f"\n- [{alert['severity'].upper()}] {alert['component']}: {alert['message']}"
        
        body += f"""

Container Status:
{json.dumps(health['containers'], indent=2)}

Resource Usage:
{json.dumps(health['resources'], indent=2)}

Please check the system immediately.
"""
        
        # Send email alert
        if self.alert_config.get('email_alerts'):
            self._send_email_alert(subject, body)
        
        # Send Slack alert
        if self.alert_config.get('slack_webhook'):
            self._send_slack_alert(subject, body)
        
        logger.warning(f"Alert sent: {subject}")

    def _send_email_alert(self, subject: str, body: str):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.alert_config['alert_email']
            msg['To'] = self.alert_config['alert_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Note: Configure SMTP settings in alert_config
            # server = smtplib.SMTP(self.alert_config['smtp_server'], self.alert_config['smtp_port'])
            # server.send_message(msg)
            
            logger.info("Email alert prepared (SMTP not configured)")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _send_slack_alert(self, subject: str, body: str):
        """Send Slack alert via webhook."""
        try:
            import requests
            
            webhook_url = self.alert_config['slack_webhook']
            payload = {
                'text': subject,
                'attachments': [{
                    'color': 'danger',
                    'text': body
                }]
            }
            
            requests.post(webhook_url, json=payload)
            logger.info("Slack alert sent")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def start_monitoring(self):
        """Start continuous health monitoring."""
        logger.info("Starting health monitoring...")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info(f"Alert threshold: {self.alert_threshold} failures")
        
        try:
            while True:
                health = self.run_health_check()
                
                logger.info(
                    f"Health Check | Status: {health['overall_status']} | "
                    f"Containers: {len([c for c in health['containers'].values() if c.get('status') == 'healthy'])}/{len(health['containers'])} | "
                    f"Watchers: {len([w for w in health['watchers'] if w['status'] == 'running'])}/{len(health['watchers'])}"
                )
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Health monitoring stopped by user")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Health Monitor')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--check', action='store_true', help='Run single health check')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path) if args.vault_path else Path(__file__).parent.parent / 'AI_Employee_Vault'
    
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}")
        return
    
    monitor = HealthMonitor(str(vault_path))
    monitor.check_interval = args.interval
    
    if args.check:
        health = monitor.run_health_check()
        print(f"\n=== Health Check Results ===\n")
        print(f"Overall Status: {health['overall_status']}")
        print(f"\nContainers:")
        for name, status in health['containers'].items():
            print(f"  {name}: {status.get('status', 'unknown')}")
        print(f"\nWatchers:")
        for watcher in health['watchers']:
            print(f"  {watcher['name']}: {watcher['status']}")
        print(f"\nResources:")
        for key, value in health['resources'].items():
            print(f"  {key}: {value}")
    
    elif args.monitor:
        monitor.start_monitoring()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
