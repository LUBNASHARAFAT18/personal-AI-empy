"""
CEO Briefing Generator - Generates weekly business audit reports.

Creates comprehensive "Monday Morning CEO Briefing" with:
- Revenue tracking and analysis
- Task completion summaries
- Bottleneck identification
- Subscription audit
- Upcoming deadlines
- Proactive suggestions

Usage:
    python ceo_briefing.py AI_Employee_Vault
    python ceo_briefing.py AI_Employee_Vault --schedule
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class CEOBriefingGenerator:
    """
    Generates comprehensive CEO briefing reports.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the briefing generator.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.briefings_folder = self.vault_path / 'Briefings'
        self.done_folder = self.vault_path / 'Done'
        self.accounting_folder = self.vault_path / 'Accounting'
        self.plans_folder = self.vault_path / 'Plans'
        self.logs_folder = self.vault_path / 'Logs'
        
        # Ensure folders exist
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

    def generate_briefing(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> Path:
        """
        Generate a comprehensive CEO briefing.

        Args:
            start_date: Start of period (default: 7 days ago)
            end_date: End of period (default: today)

        Returns:
            Path to generated briefing file
        """
        # Set date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Collect data
        revenue_data = self._analyze_revenue(start_date, end_date)
        completed_tasks = self._analyze_completed_tasks(start_date, end_date)
        bottlenecks = self._analyze_bottlenecks(start_date, end_date)
        subscriptions = self._audit_subscriptions()
        deadlines = self._get_upcoming_deadlines()
        suggestions = self._generate_suggestions(revenue_data, completed_tasks, 
                                                  bottlenecks, subscriptions)
        
        # Generate briefing
        filename = self._generate_filename(start_date, end_date)
        filepath = self.briefings_folder / filename
        
        content = self._format_briefing(
            start_date=start_date,
            end_date=end_date,
            revenue=revenue_data,
            tasks=completed_tasks,
            bottlenecks=bottlenecks,
            subscriptions=subscriptions,
            deadlines=deadlines,
            suggestions=suggestions
        )
        
        filepath.write_text(content, encoding='utf-8')
        print(f"[OK] Generated briefing: {filepath}")
        return filepath

    def _analyze_revenue(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Analyze revenue for the period.

        Returns:
            Revenue statistics dictionary
        """
        revenue = {
            'this_period': 0.0,
            'transactions': [],
            'mtm_growth': 0.0,
            'target_progress': 0.0
        }
        
        # Check accounting folder for transactions
        current_month = self.accounting_folder / f"{datetime.now().strftime('%Y-%m')}.md"
        
        if current_month.exists():
            content = current_month.read_text(encoding='utf-8')
            
            # Simple parsing for revenue entries
            for line in content.split('\n'):
                if 'revenue' in line.lower() or 'income' in line.lower():
                    # Extract amount (simple pattern matching)
                    import re
                    amounts = re.findall(r'\$?([\d,]+\.?\d*)', line)
                    for amount in amounts:
                        try:
                            revenue['this_period'] += float(amount.replace(',', ''))
                            revenue['transactions'].append({
                                'description': line.strip(),
                                'amount': float(amount.replace(',', ''))
                            })
                        except:
                            pass
        
        # Calculate MTD target progress
        business_goals = self.vault_path / 'Business_Goals.md'
        if business_goals.exists():
            content = business_goals.read_text(encoding='utf-8')
            import re
            targets = re.findall(r'Monthly.*?:.*?\$([\d,]+)', content, re.IGNORECASE)
            if targets:
                monthly_target = float(targets[0].replace(',', ''))
                revenue['monthly_target'] = monthly_target
                revenue['target_progress'] = (revenue['this_period'] / monthly_target * 100) if monthly_target > 0 else 0
        
        return revenue

    def _analyze_completed_tasks(self, start_date: datetime, 
                                 end_date: datetime) -> Dict:
        """
        Analyze completed tasks for the period.

        Returns:
            Task statistics dictionary
        """
        tasks = {
            'total': 0,
            'by_type': defaultdict(int),
            'items': []
        }
        
        if not self.done_folder.exists():
            return tasks
        
        # Scan Done folder for completed items
        for filepath in self.done_folder.glob('*.md'):
            try:
                content = filepath.read_text(encoding='utf-8')
                
                # Extract type from frontmatter
                import re
                type_match = re.search(r'type:\s*(\w+)', content)
                task_type = type_match.group(1) if type_match else 'general'
                
                # Extract created/completed dates
                created_match = re.search(r'created:\s*([\d\-T:]+)', content)
                
                tasks['total'] += 1
                tasks['by_type'][task_type] += 1
                tasks['items'].append({
                    'file': filepath.name,
                    'type': task_type,
                    'completed': filepath.stat().st_mtime
                })
                
            except Exception as e:
                continue
        
        return tasks

    def _analyze_bottlenecks(self, start_date: datetime, 
                            end_date: datetime) -> List[Dict]:
        """
        Identify bottlenecks and delays.

        Returns:
            List of bottleneck dictionaries
        """
        bottlenecks = []
        
        # Check active plans for delays
        if self.plans_folder.exists():
            for plan_file in self.plans_folder.glob('Plan_*.md'):
                content = plan_file.read_text(encoding='utf-8')
                
                # Check if plan is still in_progress
                if 'status: in_progress' in content:
                    # Check how long it's been active
                    import re
                    created_match = re.search(r'created:\s*([\d\-]+)', content)
                    if created_match:
                        try:
                            created_date = datetime.fromisoformat(created_match.group(1))
                            days_active = (datetime.now() - created_date).days
                            
                            if days_active > 3:  # More than 3 days = potential bottleneck
                                bottlenecks.append({
                                    'task': plan_file.stem,
                                    'status': 'in_progress',
                                    'days_active': days_active,
                                    'severity': 'high' if days_active > 7 else 'medium'
                                })
                        except:
                            pass
        
        return bottlenecks

    def _audit_subscriptions(self) -> List[Dict]:
        """
        Audit subscriptions for cost optimization.

        Returns:
            List of subscription dictionaries
        """
        subscriptions = []
        
        # Check Business Goals for subscription list
        business_goals = self.vault_path / 'Business_Goals.md'
        if business_goals.exists():
            content = business_goals.read_text(encoding='utf-8')
            
            # Look for subscription table
            import re
            sub_pattern = r'\|\s*([\w\s]+)\s*\|\s*\$?([\d.]+)\s*\|'
            matches = re.findall(sub_pattern, content)
            
            for name, cost in matches:
                subscriptions.append({
                    'name': name.strip(),
                    'monthly_cost': float(cost),
                    'status': 'active',
                    'last_used': 'unknown',
                    'recommendation': 'review'
                })
        
        return subscriptions

    def _get_upcoming_deadlines(self) -> List[Dict]:
        """
        Get upcoming project deadlines.

        Returns:
            List of deadline dictionaries
        """
        deadlines = []
        
        # Check Business Goals for projects
        business_goals = self.vault_path / 'Business_Goals.md'
        if business_goals.exists():
            content = business_goals.read_text(encoding='utf-8')
            
            # Look for project entries with due dates
            import re
            # Simple pattern: Project name - Due date
            project_pattern = r'([\w\s]+).*?Due[:\s]+([\w\s\d,]+)'
            matches = re.findall(project_pattern, content, re.IGNORECASE)
            
            for name, due_date in matches:
                deadlines.append({
                    'project': name.strip(),
                    'due_date': due_date.strip(),
                    'days_remaining': 'TBD'
                })
        
        return deadlines

    def _generate_suggestions(self, revenue: Dict, tasks: Dict, 
                             bottlenecks: List, subscriptions: List) -> List[Dict]:
        """
        Generate proactive suggestions based on analysis.

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        # Revenue-based suggestions
        if revenue.get('target_progress', 0) < 50:
            suggestions.append({
                'category': 'Revenue',
                'priority': 'high',
                'suggestion': f"Revenue at {revenue.get('target_progress', 0):.1f}% of monthly target. Consider accelerating client outreach.",
                'action': 'Review sales pipeline'
            })
        
        # Bottleneck-based suggestions
        for bottleneck in bottlenecks:
            if bottleneck['severity'] == 'high':
                suggestions.append({
                    'category': 'Productivity',
                    'priority': 'high',
                    'suggestion': f"Task '{bottleneck['task']}' has been in progress for {bottleneck['days_active']} days.",
                    'action': 'Review and unblock task'
                })
        
        # Subscription-based suggestions
        for sub in subscriptions:
            if sub.get('monthly_cost', 0) > 50:
                suggestions.append({
                    'category': 'Cost Optimization',
                    'priority': 'medium',
                    'suggestion': f"Review subscription '{sub['name']}' (${sub['monthly_cost']}/month).",
                    'action': 'Verify usage and necessity'
                })
        
        return suggestions

    def _generate_filename(self, start_date: datetime, end_date: datetime) -> str:
        """Generate briefing filename."""
        # Get day of week for end date
        day_name = end_date.strftime('%A')
        date_str = end_date.strftime('%Y-%m-%d')
        return f"{date_str}_{day_name}_Briefing.md"

    def _format_briefing(self, **kwargs) -> str:
        """Format briefing as markdown."""
        start = kwargs['start_date']
        end = kwargs['end_date']
        revenue = kwargs['revenue']
        tasks = kwargs['tasks']
        bottlenecks = kwargs['bottlenecks']
        subscriptions = kwargs['subscriptions']
        deadlines = kwargs['deadlines']
        suggestions = kwargs['suggestions']
        
        # Executive summary
        summary = self._generate_executive_summary(revenue, tasks, bottlenecks)
        
        content = f'''---
generated: {datetime.now().isoformat()}
period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}
type: ceo_briefing
---

# Monday Morning CEO Briefing

> **Period:** {start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}

---

## Executive Summary

{summary}

---

## 📊 Revenue Analysis

### This Period
- **Total Revenue:** ${revenue['this_period']:,.2f}
- **Transactions:** {len(revenue.get('transactions', []))}

### Monthly Target Progress
- **MTD Revenue:** ${revenue['this_period']:,.2f}
- **Monthly Target:** ${revenue.get('monthly_target', 0):,.2f}
- **Progress:** {revenue.get('target_progress', 0):.1f}%

---

## ✅ Completed Tasks

### Summary
- **Total Tasks:** {tasks['total']}
- **By Type:**
{self._format_task_breakdown(tasks['by_type'])}

### Recent Completions
{self._format_recent_tasks(tasks['items'][:5])}

---

## 🚧 Bottlenecks Identified

{self._format_bottlenecks(bottlenecks) if bottlenecks else '*No significant bottlenecks detected.*'}

---

## 💳 Subscription Audit

{self._format_subscriptions(subscriptions) if subscriptions else '*No subscriptions tracked.*'}

---

## 📅 Upcoming Deadlines

{self._format_deadlines(deadlines) if deadlines else '*No upcoming deadlines.*'}

---

## 💡 Proactive Suggestions

{self._format_suggestions(suggestions) if suggestions else '*No suggestions at this time.*'}

---

## 📈 Week Over Week Comparison

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Revenue | ${revenue['this_period']:,.2f} | $0.00 | - |
| Tasks Completed | {tasks['total']} | 0 | - |
| Bottlenecks | {len(bottlenecks)} | 0 | - |

---

## 🎯 Action Items for This Week

1. Review and address identified bottlenecks
2. Follow up on pending approvals
3. Accelerate revenue-generating activities
4. Review subscription costs

---

*Briefing generated by AI Employee v0.3 (Gold Tier)*
*Next briefing: {(end + timedelta(days=7)).strftime('%Y-%m-%d')}*
'''
        
        return content

    def _generate_executive_summary(self, revenue: Dict, tasks: Dict, 
                                   bottlenecks: List) -> str:
        """Generate executive summary text."""
        parts = []
        
        # Revenue assessment
        if revenue.get('target_progress', 0) >= 80:
            parts.append("Excellent revenue performance.")
        elif revenue.get('target_progress', 0) >= 50:
            parts.append("Revenue on track.")
        else:
            parts.append("Revenue needs attention.")
        
        # Task assessment
        if tasks['total'] >= 10:
            parts.append("High productivity this week.")
        elif tasks['total'] >= 5:
            parts.append("Steady task completion.")
        else:
            parts.append("Task completion below target.")
        
        # Bottleneck assessment
        if len(bottlenecks) > 3:
            parts.append("Multiple bottlenecks require immediate attention.")
        elif len(bottlenecks) > 0:
            parts.append("Few bottlenecks identified.")
        
        return " ".join(parts)

    def _format_task_breakdown(self, by_type: Dict) -> str:
        """Format task breakdown by type."""
        if not by_type:
            return "  *No tasks categorized*"
        
        lines = []
        for task_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - **{task_type.title()}:** {count}")
        return '\n'.join(lines)

    def _format_recent_tasks(self, items: List) -> str:
        """Format recent tasks list."""
        if not items:
            return '*No recent tasks*'
        
        lines = []
        for item in items:
            lines.append(f"- [x] {item['file']} ({item['type']})")
        return '\n'.join(lines)

    def _format_bottlenecks(self, bottlenecks: List) -> str:
        """Format bottlenecks table."""
        if not bottlenecks:
            return '*No bottlenecks*'
        
        lines = ["| Task | Status | Days Active | Severity |", "|------|--------|-------------|----------|"]
        for b in bottlenecks:
            lines.append(f"| {b['task']} | {b['status']} | {b['days_active']} | {b['severity'].upper()} |")
        return '\n'.join(lines)

    def _format_subscriptions(self, subscriptions: List) -> str:
        """Format subscriptions table."""
        if not subscriptions:
            return '*No subscriptions*'
        
        lines = ["| Service | Monthly Cost | Status | Recommendation |", "|---------|--------------|--------|----------------|"]
        for sub in subscriptions:
            lines.append(f"| {sub['name']} | ${sub['monthly_cost']:.2f} | {sub['status']} | {sub.get('recommendation', 'review')} |")
        
        total = sum(s['monthly_cost'] for s in subscriptions)
        lines.append(f"\n**Total Monthly:** ${total:.2f}")
        lines.append(f"**Total Annual:** ${total * 12:.2f}")
        
        return '\n'.join(lines)

    def _format_deadlines(self, deadlines: List) -> str:
        """Format deadlines list."""
        if not deadlines:
            return '*No deadlines*'
        
        lines = []
        for d in deadlines:
            lines.append(f"- **{d['project']}:** Due {d['due_date']} ({d['days_remaining']} days)")
        return '\n'.join(lines)

    def _format_suggestions(self, suggestions: List) -> str:
        """Format suggestions list."""
        if not suggestions:
            return '*No suggestions*'
        
        lines = []
        for i, s in enumerate(suggestions, 1):
            lines.append(f"### {i}. {s['category']} - {s['priority'].upper()} Priority")
            lines.append(f"{s['suggestion']}")
            lines.append(f"**Action:** {s['action']}")
            lines.append("")
        
        return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--schedule', action='store_true', help='Schedule weekly briefing')
    
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
    
    generator = CEOBriefingGenerator(str(vault_path))
    
    if args.schedule:
        # Schedule via task scheduler
        scheduler_script = vault_path / 'watchers' / 'task_scheduler.py'
        if scheduler_script.exists():
            os.system(f'python "{scheduler_script}" {vault_path} --install --task weekly-briefing --day monday --time 08:00')
        else:
            print("Task Scheduler not found. Run manually:")
            print(f"  python task_scheduler.py {vault_path} --install --task weekly-briefing --day monday --time 08:00")
    else:
        # Generate dates
        start_date = None
        end_date = None
        
        if args.start_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        if args.end_date:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        print(f"=== CEO Briefing Generator ===")
        print(f"Vault: {vault_path}")
        print(f"Period: {start_date or '7 days ago'} to {end_date or 'today'}")
        
        briefing_path = generator.generate_briefing(start_date, end_date)
        
        print(f"\n[OK] Briefing generated successfully!")
        print(f"Location: {briefing_path}")


if __name__ == '__main__':
    main()
