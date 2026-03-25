"""
WhatsApp Watcher - Monitors WhatsApp Web for new messages with urgent keywords.

Uses Playwright for browser automation. Session is persisted to avoid repeated QR scans.
When urgent messages are detected, creates action files in Needs_Action folder.

⚠️ WARNING: Using automated tools with WhatsApp may violate Terms of Service.
Use at your own risk and with reasonable rate limiting.

Usage:
    python whatsapp_watcher.py /path/to/vault --setup-session  # First-time auth
    python whatsapp_watcher.py /path/to/vault                  # Start monitoring
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages containing urgent keywords.
    """

    def __init__(self, vault_path: str, session_path: Optional[str] = None,
                 check_interval: int = 30, keywords: Optional[List[str]] = None,
                 headless: bool = True):
        """
        Initialize the WhatsApp watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to save/load browser session (default: ./whatsapp_session)
            check_interval: Seconds between checks (default: 30)
            keywords: List of keywords to detect (default: urgent keywords)
            headless: Run browser in headless mode (default: True)
        """
        super().__init__(vault_path, check_interval)
        
        self.session_path = Path(session_path) if session_path else Path(__file__).parent / 'whatsapp_session'
        self.keywords = keywords or ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency', 'money', 'deadline']
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
        # Track processed messages
        self.processed_messages = set()

    def setup_session(self):
        """
        Set up WhatsApp session by showing QR code for authentication.
        """
        print("Starting WhatsApp session setup...")
        print("A browser window will open showing the QR code.")
        print("Scan it with your phone's WhatsApp app.")
        print("Wait for 'WhatsApp Web connected' message, then close the browser.\n")
        
        with sync_playwright() as p:
            # Launch browser with persistent context
            self.context = p.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                viewport={'width': 1280, 'height': 720}
            )
            
            self.page = self.context.pages[0]
            self.page.goto('https://web.whatsapp.com')
            
            print("\nWaiting for WhatsApp Web to load...")
            print("Scan the QR code now...")
            
            # Wait for chat list to appear (indicates successful login)
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=120000)
                print("\n[OK] WhatsApp Web connected!")
                print(f"Session saved to: {self.session_path}")
                print("\nYou can now run the watcher without --setup-session flag")
            except PlaywrightTimeout:
                print("\n[FAIL] QR code scan timed out. Please try again.")
            
            self.context.close()

    def _launch_browser(self) -> bool:
        """
        Launch browser and navigate to WhatsApp Web.

        Returns:
            True if successful
        """
        try:
            with sync_playwright() as p:
                self.context = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=self.headless,
                    viewport={'width': 1280, 'height': 720}
                )
                
                self.page = self.context.pages[0]
                self.page.goto('https://web.whatsapp.com')
                
                # Wait for chat list
                try:
                    self.page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                    return True
                except PlaywrightTimeout:
                    self.logger.error("WhatsApp Web did not load. Session may need re-authentication.")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error launching browser: {e}")
            return False

    def _close_browser(self):
        """Close browser and context."""
        if self.context:
            try:
                self.context.close()
            except:
                pass
        self.browser = None
        self.context = None
        self.page = None

    def check_for_updates(self) -> list:
        """
        Check WhatsApp for new messages with urgent keywords.

        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Launch browser if not already open
        if not self.page:
            if not self._launch_browser():
                return []
        
        try:
            # Wait for chat list
            self.page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)
            
            # Find all chat items with unread indicators
            # WhatsApp Web structure may change, so we use multiple selectors
            chat_selectors = [
                '[aria-label*="unread"]',
                '[data-testid="chat-list"] > div[role="row"]',
                'div[tabindex="0"]'
            ]
            
            chats = []
            for selector in chat_selectors:
                try:
                    chats = self.page.query_selector_all(selector)
                    if chats:
                        break
                except:
                    continue
            
            for chat in chats:
                try:
                    # Extract chat info
                    chat_text = chat.inner_text(timeout=2000)
                    
                    # Check for unread indicator
                    is_unread = False
                    try:
                        # Look for unread badge or green dot
                        unread_indicators = [
                            chat.query_selector('[aria-label*="unread"]'),
                            chat.query_selector('[data-testid="unread-mark"]'),
                            chat.query_selector('span:has-text("unread")')
                        ]
                        is_unread = any(indicator for indicator in unread_indicators)
                    except:
                        pass
                    
                    # Check for keywords
                    chat_text_lower = chat_text.lower()
                    matched_keywords = [kw for kw in self.keywords if kw in chat_text_lower]
                    
                    if matched_keywords:
                        # Extract chat name/number
                        chat_name = "Unknown"
                        try:
                            name_element = chat.query_selector('[dir="auto"]')
                            if name_element:
                                chat_name = name_element.inner_text(timeout=1000)[:50]
                        except:
                            pass
                        
                        # Create unique ID
                        timestamp = int(time.time())
                        unique_id = f"{chat_name.replace(' ', '_')}_{timestamp}"
                        
                        if unique_id not in self.processed_messages:
                            messages.append({
                                'chat_name': chat_name,
                                'text': chat_text,
                                'keywords': matched_keywords,
                                'timestamp': timestamp,
                                'unique_id': unique_id
                            })
                            self.processed_messages.add(unique_id)
                
                except Exception as e:
                    self.logger.debug(f"Error processing chat: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            # Try to recover by closing and reopening browser
            self._close_browser()
        
        return messages

    def create_action_file(self, message: dict) -> Path:
        """
        Create an action file for a WhatsApp message.

        Args:
            message: Message dictionary with chat_name, text, keywords, timestamp

        Returns:
            Path to created action file
        """
        # Determine priority based on keywords
        high_priority_keywords = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'money']
        priority = 'high' if any(kw in message['keywords'] for kw in high_priority_keywords) else 'medium'
        
        # Format timestamp
        received = datetime.fromtimestamp(message['timestamp']).isoformat()
        
        # Create action file
        action_filename = self.generate_filename('WHATSAPP', message['unique_id'])
        action_path = self.needs_action / action_filename
        
        content = f'''{self.create_frontmatter(
            item_type='whatsapp',
            priority=priority,
            from_=f'"{message["chat_name"]}"',
            chat=f'"{message["chat_name"]}"',
            received=received,
            keywords='", "'.join(message['keywords'])
        )}

## Message Information

- **From:** {message['chat_name']}
- **Chat:** {message['chat_name']}
- **Received:** {received}
- **Priority:** {priority.upper()}
- **Keywords Detected:** {', '.join(message['keywords'])}

## Message Content

```
{message['text']}
```

## Suggested Actions

- [ ] Read message and understand context
- [ ] Check if immediate response needed
- [ ] Draft reply (save to Pending_Approval if sensitive)
- [ ] Take required action
- [ ] Follow up if needed

## Notes

*Add your notes here...*

---
*Generated by WhatsApp Watcher v0.1*
'''
        
        action_path.write_text(content, encoding='utf-8')
        return action_path

    def run(self):
        """
        Main run loop - continuously monitors WhatsApp Web.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info(f'Keywords: {self.keywords}')
        
        # Check if session exists
        if not self.session_path.exists():
            self.logger.error("Session folder not found. Run with --setup-session first.")
            return
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f'Found {len(items)} urgent message(s)')
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f'Created action file: {filepath.name}')
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                    else:
                        self.logger.debug('No new urgent messages')
                except Exception as e:
                    self.logger.error(f'Error in check cycle: {e}')
                    # Attempt recovery
                    self._close_browser()

                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
            self._close_browser()
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            self._close_browser()
            raise
        finally:
            self._close_browser()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='WhatsApp Watcher for AI Employee')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--setup-session', action='store_true', help='Set up WhatsApp session (QR scan)')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--keywords', type=str, help='Comma-separated keywords to detect')
    parser.add_argument('--session-path', type=str, help='Path to store browser session')
    parser.add_argument('--headless', type=str, default='true', help='Run browser headless (true/false)')
    
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
    
    # Parse keywords
    keywords = None
    if args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split(',')]
    
    # Parse headless
    headless = args.headless.lower() == 'true'
    
    print(f"=== AI Employee WhatsApp Watcher ===")
    print(f"Vault: {vault_path}")
    print(f"Session: {args.session_path or './whatsapp_session'}")
    print(f"Check interval: {args.interval}s")
    print(f"Keywords: {keywords or ['urgent', 'asap', 'invoice', 'payment', 'help']}")
    print(f"Headless: {headless}")
    
    watcher = WhatsAppWatcher(
        str(vault_path),
        session_path=args.session_path,
        check_interval=args.interval,
        keywords=keywords,
        headless=headless
    )
    
    if args.setup_session:
        watcher.setup_session()
    else:
        print(f"\nMonitoring: WhatsApp Web")
        print(f"Output: {vault_path / 'Needs_Action'}")
        print(f"Press Ctrl+C to stop\n")
        watcher.run()


if __name__ == '__main__':
    main()
