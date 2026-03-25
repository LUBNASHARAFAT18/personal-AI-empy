"""
LinkedIn Poster - Automatically posts business updates to LinkedIn.

Uses Playwright for browser automation. Supports:
- Creating posts with approval workflow (HITL pattern)
- Scheduled posting at optimal times
- Session persistence for repeated use
- Content generation from business goals

⚠️ WARNING: Using automated tools with LinkedIn may violate Terms of Service.
Use at your own risk and with reasonable rate limiting.

Usage:
    python linkedin_poster.py /path/to/vault --login           # First-time auth
    python linkedin_poster.py /path/to/vault --create-post "Hello"  # Create draft
    python linkedin_poster.py /path/to/vault --post            # Post approved content
"""

import os
import sys
import time
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


class LinkedInPoster:
    """
    Posts content to LinkedIn using browser automation.
    """

    def __init__(self, vault_path: str, session_path: Optional[str] = None,
                 headless: bool = True, max_posts_per_day: int = 3):
        """
        Initialize the LinkedIn poster.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to save/load browser session (default: ./linkedin_session)
            headless: Run browser in headless mode (default: True)
            max_posts_per_day: Maximum posts per day (default: 3)
        """
        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path) if session_path else Path(__file__).parent / 'linkedin_session'
        self.headless = headless
        self.max_posts_per_day = max_posts_per_day
        
        # Folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        
        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.done]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.context = None
        self.page = None

    def login(self):
        """
        Log in to LinkedIn and save session.
        """
        print("Starting LinkedIn login...")
        print("A browser window will open. Log in to LinkedIn normally.")
        print("After successful login, the browser will close automatically.\n")
        
        with sync_playwright() as p:
            self.context = p.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                viewport={'width': 1280, 'height': 720}
            )
            
            self.page = self.context.pages[0]
            self.page.goto('https://www.linkedin.com/login')
            
            print("\nWaiting for login...")
            print("Log in to LinkedIn in the browser window.")
            
            # Wait for navigation to feed page (indicates successful login)
            try:
                self.page.wait_for_url('https://www.linkedin.com/feed/*', timeout=300000)
                print("\n[OK] LinkedIn login successful!")
                print(f"Session saved to: {self.session_path}")
            except PlaywrightTimeout:
                print("\n[FAIL] Login timed out. Please try again.")
            
            # Wait a moment for session to save
            time.sleep(2)
            self.context.close()

    def _launch_browser(self) -> bool:
        """
        Launch browser and navigate to LinkedIn.

        Returns:
            True if successful and logged in
        """
        try:
            with sync_playwright() as p:
                self.context = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=self.headless,
                    viewport={'width': 1280, 'height': 720}
                )
                
                self.page = self.context.pages[0]
                self.page.goto('https://www.linkedin.com')
                
                # Check if logged in by looking for feed
                try:
                    self.page.wait_for_selector('[data-id="voyager-nav-element-feed"]', timeout=10000)
                    return True
                except PlaywrightTimeout:
                    # Might be on login page
                    if 'login' in self.page.url:
                        print("Not logged in. Run with --login first.")
                        return False
                    return True  # Already on LinkedIn
                    
        except Exception as e:
            print(f"Error launching browser: {e}")
            return False

    def _close_browser(self):
        """Close browser and context."""
        if self.context:
            try:
                self.context.close()
            except:
                pass
        self.context = None
        self.page = None

    def create_post_draft(self, content: str, hashtags: str = "", 
                          scheduled_time: Optional[str] = None) -> Path:
        """
        Create a post draft with approval workflow.

        Args:
            content: Post content
            hashtags: Hashtags (space or comma separated)
            scheduled_time: Optional scheduled time (ISO format)

        Returns:
            Path to created approval file
        """
        # Format hashtags
        if hashtags:
            if ',' in hashtags:
                hashtag_list = [h.strip() for h in hashtags.split(',')]
            else:
                hashtag_list = hashtags.split()
            hashtags_formatted = ' '.join(hashtag_list)
        else:
            hashtags_formatted = ""
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"PENDING_APPROVAL_LinkedIn_Post_{timestamp}.md"
        filepath = self.pending_approval / filename
        
        # Format scheduled time
        if not scheduled_time:
            scheduled_time = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1)
        scheduled_str = scheduled_time if isinstance(scheduled_time, str) else scheduled_time.isoformat()
        
        content_md = f'''---
type: approval_request
action: linkedin_post
content: |
{chr(10).join('  ' + line for line in content.split(chr(10)))}
hashtags: "{hashtags_formatted}"
scheduled_time: {scheduled_str}
created: {datetime.now().isoformat()}
status: pending
---

# LinkedIn Post Approval Required

## Post Preview

**Content:**
{content}

**Hashtags:**
{hashtags_formatted if hashtags_formatted else "(none)"}

**Scheduled For:**
{scheduled_str}

## Instructions

### To Approve
1. Review the content above
2. Move this file to `Approved/` folder
3. AI will post automatically when detected

### To Reject
1. Move this file to `Rejected/` folder
2. Add reason for rejection in notes below

## Notes

*Add rejection reason or comments here...*

---
*Generated by LinkedIn Poster v0.1*
'''
        
        filepath.write_text(content_md, encoding='utf-8')
        print(f"[OK] Created approval file: {filepath}")
        return filepath

    def post_content(self, content: str, hashtags: str = "") -> bool:
        """
        Post content to LinkedIn.

        Args:
            content: Post content
            hashtags: Hashtags

        Returns:
            True if post successful
        """
        if not self.page:
            if not self._launch_browser():
                return False
        
        try:
            # Navigate to LinkedIn
            self.page.goto('https://www.linkedin.com')
            time.sleep(2)
            
            # Click on "Start a post" box
            try:
                # Try multiple selectors for the post input
                post_selectors = [
                    '[data-test-id="feed-compose-box"]',
                    '.share-box-feed-entry__trigger',
                    'button:has-text("Start a post")',
                    'button:has-text("Create a post")'
                ]
                
                clicked = False
                for selector in post_selectors:
                    try:
                        self.page.click(selector, timeout=5000)
                        clicked = True
                        break
                    except:
                        continue
                
                if not clicked:
                    print("Could not find post creation button")
                    return False
                
                time.sleep(2)
                
                # Find the text editor and type content
                editor_selectors = [
                    'div[contenteditable="true"]',
                    '.ql-editor[contenteditable="true"]',
                    '[aria-label*="What do you want to share?"]'
                ]
                
                typed = False
                for selector in editor_selectors:
                    try:
                        editor = self.page.query_selector(selector)
                        if editor:
                            editor.fill(content)
                            typed = True
                            break
                    except:
                        continue
                
                if not typed:
                    print("Could not find text editor")
                    return False
                
                time.sleep(1)
                
                # Add hashtags if provided
                if hashtags:
                    hashtag_list = hashtags.replace(',', ' ').split()
                    for hashtag in hashtag_list[:5]:  # Max 5 hashtags
                        if not hashtag.startswith('#'):
                            hashtag = f'#{hashtag}'
                        # Type hashtag in editor
                        self.page.keyboard.type(f' {hashtag}')
                        time.sleep(0.5)
                
                time.sleep(2)
                
                # Click Post button
                post_selectors = [
                    'button:has-text("Post")',
                    'button:has-text("Share")'
                ]
                
                posted = False
                for selector in post_selectors:
                    try:
                        self.page.click(selector, timeout=5000)
                        posted = True
                        break
                    except:
                        continue
                
                if posted:
                    print("[OK] Post submitted successfully!")
                    time.sleep(3)  # Wait for post to complete
                    return True
                else:
                    print("Could not find Post button")
                    return False
                    
            except Exception as e:
                print(f"Error during posting: {e}")
                return False
                
        finally:
            self._close_browser()

    def check_approved_posts(self) -> List[Path]:
        """
        Check Approved folder for posts to publish.

        Returns:
            List of approval file paths
        """
        approved_files = list(self.approved.glob('PENDING_APPROVAL_LinkedIn_Post_*.md'))
        return approved_files

    def process_approved_post(self, filepath: Path) -> bool:
        """
        Process an approved post file.

        Args:
            filepath: Path to approval file

        Returns:
            True if post successful
        """
        content = filepath.read_text(encoding='utf-8')
        
        # Parse frontmatter (simple parsing)
        lines = content.split('\n')
        in_frontmatter = False
        frontmatter_end = 0
        post_content = []
        hashtags = ""
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    frontmatter_end = i
                    break
            elif in_frontmatter:
                if line.startswith('hashtags:'):
                    hashtags = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('content:'):
                    # Content might be on same line or following lines
                    pass
        
        # Get content from after frontmatter
        content_lines = lines[frontmatter_end + 1:]
        
        # Find content section
        in_content = False
        for line in content_lines:
            if line.startswith('**Content:**'):
                in_content = True
                continue
            elif line.startswith('**Hashtags:**') or line.startswith('---'):
                break
            elif in_content and line.strip():
                post_content.append(line.strip())
        
        full_content = '\n'.join(post_content)
        
        if not full_content:
            print(f"Warning: Could not extract content from {filepath}")
            return False
        
        print(f"Posting to LinkedIn...")
        print(f"Content: {full_content[:100]}...")
        
        success = self.post_content(full_content, hashtags)
        
        if success:
            # Move to Done folder
            done_path = self.done / filepath.name
            filepath.rename(done_path)
            print(f"[OK] Post completed. File moved to Done folder.")
        else:
            print(f"[FAIL] Post failed. File remains in Approved folder.")
        
        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LinkedIn Poster for AI Employee')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--login', action='store_true', help='Log in to LinkedIn (save session)')
    parser.add_argument('--create-post', type=str, help='Create a post draft with content')
    parser.add_argument('--create-post-file', type=str, help='Create post from markdown file')
    parser.add_argument('--hashtags', type=str, default='', help='Hashtags for post')
    parser.add_argument('--post', action='store_true', help='Post approved content')
    parser.add_argument('--schedule', action='store_true', help='Run in scheduling mode')
    parser.add_argument('--schedule-times', type=str, default='09:00,15:00,18:00', help='Schedule times (comma-separated)')
    parser.add_argument('--headless', type=str, default='true', help='Run browser headless (true/false)')
    parser.add_argument('--dry-run', action='store_true', help='Create draft without posting')
    
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
    
    # Parse headless
    headless = args.headless.lower() == 'true'
    
    poster = LinkedInPoster(str(vault_path), headless=headless)
    
    if args.login:
        poster.login()
    
    elif args.create_post:
        poster.create_post_draft(args.create_post, args.hashtags)
    
    elif args.create_post_file:
        file_path = Path(args.create_post_file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        content = file_path.read_text(encoding='utf-8')
        poster.create_post_draft(content, args.hashtags)
    
    elif args.post:
        print("Checking for approved posts...")
        approved = poster.check_approved_posts()
        if approved:
            for filepath in approved:
                poster.process_approved_post(filepath)
        else:
            print("No approved posts found in Approved/ folder.")
    
    elif args.schedule:
        print(f"=== LinkedIn Poster Scheduler ===")
        print(f"Vault: {vault_path}")
        print(f"Schedule times: {args.schedule_times}")
        print(f"Press Ctrl+C to stop\n")
        
        schedule_times = [t.strip() for t in args.schedule_times.split(',')]
        
        try:
            while True:
                now = datetime.now()
                current_time = f"{now.hour:02d}:{now.minute:02d}"
                
                if current_time in schedule_times:
                    print(f"[{now.isoformat()}] Checking for approved posts...")
                    approved = poster.check_approved_posts()
                    for filepath in approved:
                        poster.process_approved_post(filepath)
                    # Wait a minute to avoid duplicate posts
                    time.sleep(60)
                else:
                    time.sleep(30)  # Check every 30 seconds
                    
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
