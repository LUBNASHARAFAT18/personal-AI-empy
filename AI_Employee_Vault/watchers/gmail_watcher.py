"""
Gmail Watcher - Monitors Gmail for new, unread, and important emails.

When new emails are detected:
1. Fetches email content via Gmail API
2. Detects priority based on keywords
3. Creates action file in Needs_Action folder
4. Optionally marks email as read

Usage:
    python gmail_watcher.py /path/to/vault --authenticate  # First-time auth
    python gmail_watcher.py /path/to/vault                # Start monitoring

Version: 0.2 (Updated 2026-03-13)
"""

import os
import sys
import base64
import argparse
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional, List

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from base_watcher import BaseWatcher


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_WITH_SEND = ['https://www.googleapis.com/auth/gmail.modify']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for new, unread, and important emails.
    
    Features:
    - OAuth2 authentication with token refresh
    - Priority detection based on keywords
    - Duplicate prevention
    - Configurable check interval and filters
    - Error recovery and logging
    """

    def __init__(self, vault_path: str, credentials_path: Path, 
                 token_path: Optional[Path] = None, check_interval: int = 120,
                 label_filter: str = 'IMPORTANT', max_results: int = 10):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to OAuth2 credentials.json
            token_path: Path to save/load token.json (default: same dir as credentials)
            check_interval: Seconds between checks (default: 120)
            label_filter: Gmail label to filter (default: IMPORTANT)
            max_results: Maximum emails to fetch per check (default: 10)
        """
        super().__init__(vault_path, check_interval)
        
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else self.credentials_path.parent / 'token.json'
        self.label_filter = label_filter
        self.max_results = max_results
        self.service = None
        self.creds = None
        
        # Priority keywords
        self.high_priority_keywords = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'due', 'overdue']
        self.medium_priority_keywords = ['deadline', 'today', 'tomorrow', 'meeting', 'call', 'schedule', 'reminder']
        
        # Statistics
        self.emails_processed = 0
        self.last_check_time = None

    def authenticate(self) -> bool:
        """
        Perform OAuth2 authentication and save token.

        Returns:
            True if authentication successful
        """
        self.logger.info("Starting OAuth2 authentication...")
        self.creds = None

        # Load existing token
        if self.token_path.exists():
            self.logger.info(f"Loading existing token from {self.token_path}")
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES_WITH_SEND)

        # Refresh or authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired:
                self.logger.info("Token expired, attempting refresh...")
                try:
                    self.creds.refresh(Request())
                    self.logger.info("Token refreshed successfully")
                except RefreshError as e:
                    self.logger.warning(f"Token refresh failed: {e}")
                    self.creds = None

            if not self.creds:
                self.logger.info("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES_WITH_SEND
                )
                self.creds = flow.run_local_server(port=0, host='localhost')
                self.logger.info("OAuth2 flow completed")

            # Save token
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as f:
                f.write(self.creds.to_json())
            self.logger.info(f"Token saved to {self.token_path}")
        
        # Build service
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.logger.info("Gmail service initialized")
        return True

    def check_for_updates(self) -> list:
        """
        Check Gmail for new, unread, important messages.

        Returns:
            List of message dictionaries
        """
        if not self.service:
            self.logger.info("Initializing Gmail service...")
            if not self.authenticate():
                return []
        
        try:
            # Query for unread + important messages
            query = 'is:unread'
            if self.label_filter:
                query += f' label:{self.label_filter}'
            
            self.logger.debug(f"Executing query: {query}")
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
            ).execute()
            
            messages = results.get('messages', [])
            self.last_check_time = datetime.now()
            
            # Filter out already processed
            new_messages = []
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)
                    self.processed_ids.add(msg['id'])
            
            if new_messages:
                self.logger.info(f"Found {len(new_messages)} new message(s)")
            else:
                self.logger.debug("No new messages")
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            # Try to recover by re-authenticating
            self.service = None
            return []

    def create_action_file(self, message: dict) -> Path:
        """
        Create an action file for an email.

        Args:
            message: Gmail message dict

        Returns:
            Path to created action file
        """
        if not self.service:
            self.authenticate()
        
        # Fetch full message
        msg = self.service.users().messages().get(
            userId='me',
            id=message['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        from_addr = headers.get('From', 'Unknown')
        subject = headers.get('Subject', 'No Subject')
        date_str = headers.get('Date', '')
        to_addr = headers.get('To', '')
        
        try:
            received = parsedate_to_datetime(date_str).isoformat() if date_str else datetime.now().isoformat()
        except Exception:
            received = datetime.now().isoformat()
        
        # Extract body
        body = self._extract_body(msg['payload'])
        
        # Determine priority
        priority = self._detect_priority(subject, body)
        
        # Create action file content
        unique_id = message['id'][:12]
        action_filename = self.generate_filename('EMAIL', unique_id)
        action_path = self.needs_action / action_filename
        
        content = f'''{self.create_frontmatter(
            item_type='email',
            priority=priority,
            from_=f'"{from_addr}"',
            to=f'"{to_addr}"',
            subject=f'"{subject}"',
            received=received,
            message_id=message['id']
        )}

## Email Information

- **From:** {from_addr}
- **To:** {to_addr}
- **Subject:** {subject}
- **Received:** {received}
- **Priority:** {priority.upper()}
- **Message ID:** {message['id']}

## Email Content

{body}

## Suggested Actions

- [ ] Read and understand email
- [ ] Draft reply (save to Pending_Approval if sensitive)
- [ ] Forward to relevant party if needed
- [ ] Create follow-up task if required
- [ ] Archive after processing

## Notes

*Add your notes here...*

---
*Generated by Gmail Watcher v0.2*
'''
        
        action_path.write_text(content, encoding='utf-8')
        self.emails_processed += 1
        return action_path

    def _extract_body(self, payload: dict) -> str:
        """
        Extract plain text body from email payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        # Try plain text first
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        
        # Try parts (multipart)
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
            
            # Fallback to HTML
            for part in payload['parts']:
                if part['mimeType'] == 'text/html' and 'data' in part['body']:
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                    return self._strip_html(html)
        
        return '[No text content available]'

    def _strip_html(self, html: str) -> str:
        """
        Simple HTML to text conversion.

        Args:
            html: HTML string

        Returns:
            Plain text
        """
        import re
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all tags
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _detect_priority(self, subject: str, body: str) -> str:
        """
        Detect email priority based on keywords.

        Args:
            subject: Email subject
            body: Email body

        Returns:
            'high', 'medium', or 'low'
        """
        text = f"{subject} {body}".lower()
        
        if any(kw in text for kw in self.high_priority_keywords):
            return 'high'
        elif any(kw in text for kw in self.medium_priority_keywords):
            return 'medium'
        else:
            return 'medium'

    def mark_as_read(self, message_id: str):
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID
        """
        if not self.service:
            self.authenticate()
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f'Marked message {message_id} as read')
        except Exception as e:
            self.logger.error(f'Error marking message as read: {e}')

    def get_stats(self) -> dict:
        """
        Get watcher statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'emails_processed': self.emails_processed,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'check_interval': self.check_interval,
            'label_filter': self.label_filter,
            'max_results': self.max_results
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--authenticate', action='store_true', help='Run OAuth2 authentication')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    parser.add_argument('--label', default='IMPORTANT', help='Gmail label to filter')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum emails to fetch per check')
    parser.add_argument('--credentials', help='Path to credentials.json')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--stats', action='store_true', help='Show statistics after run')
    
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
    
    # Get credentials path
    if args.credentials:
        credentials_path = Path(args.credentials)
    else:
        # Look for credentials in common locations
        possible_paths = [
            Path(__file__).parent / 'credentials.json',
            vault_path / 'credentials.json',
            Path.home() / '.credentials' / 'gmail' / 'credentials.json',
        ]
        credentials_path = None
        for p in possible_paths:
            if p.exists():
                credentials_path = p
                break
        
        if not credentials_path:
            print("Error: credentials.json not found.")
            print("Please download from Google Cloud Console and place in:")
            print("  - watchers/credentials.json")
            print("  - AI_Employee_Vault/credentials.json")
            print("  - ~/.credentials/gmail/credentials.json")
            print("\nOr specify with --credentials flag")
            sys.exit(1)
    
    # Ensure credentials_path is a Path object
    if not isinstance(credentials_path, Path):
        credentials_path = Path(credentials_path)
    
    print(f"=== AI Employee Gmail Watcher v0.2 ===")
    print(f"Vault: {vault_path}")
    print(f"Credentials: {credentials_path}")
    print(f"Check interval: {args.interval}s")
    print(f"Label filter: {args.label}")
    print(f"Max results: {args.max_results}")
    
    if args.authenticate:
        print("\nStarting OAuth2 authentication...")
        print("A browser window will open for Google login.")
        print("Grant permissions and return here.\n")
        
        watcher = GmailWatcher(
            str(vault_path),
            str(credentials_path),
            check_interval=args.interval,
            label_filter=args.label,
            max_results=args.max_results
        )
        
        if watcher.authenticate():
            print("\n[OK] Authentication successful!")
            print(f"Token saved to: {watcher.token_path}")
            print("\nYou can now run the watcher without --authenticate flag")
        else:
            print("\n[FAIL] Authentication failed")
            sys.exit(1)
    elif args.test:
        print("\nRunning test mode...")
        watcher = GmailWatcher(
            str(vault_path),
            str(credentials_path),
            check_interval=args.interval,
            label_filter=args.label,
            max_results=args.max_results
        )
        
        if not watcher.token_path.exists():
            print("Error: Token not found. Run with --authenticate first.")
            sys.exit(1)
        
        watcher.authenticate()
        messages = watcher.check_for_updates()
        
        if messages:
            print(f"Found {len(messages)} message(s)")
            for msg in messages:
                filepath = watcher.create_action_file(msg)
                print(f"  Created: {filepath.name}")
        else:
            print("No new messages found")
        
        stats = watcher.get_stats()
        print(f"\nStatistics:")
        print(f"  Emails processed: {stats['emails_processed']}")
        
    else:
        print(f"\nMonitoring: Gmail inbox ({args.label})")
        print(f"Output: {vault_path / 'Needs_Action'}")
        print(f"Press Ctrl+C to stop\n")
        
        watcher = GmailWatcher(
            str(vault_path),
            str(credentials_path),
            check_interval=args.interval,
            label_filter=args.label,
            max_results=args.max_results
        )
        
        try:
            watcher.run()
        except KeyboardInterrupt:
            print("\n[OK] Gmail Watcher stopped by user")
        
        if args.stats:
            stats = watcher.get_stats()
            print(f"\nFinal Statistics:")
            print(f"  Emails processed: {stats['emails_processed']}")
            print(f"  Last check: {stats['last_check_time']}")


if __name__ == '__main__':
    main()
