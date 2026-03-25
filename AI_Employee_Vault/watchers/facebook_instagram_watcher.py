"""
Facebook & Instagram Watcher - Posts to Meta platforms.

Uses Meta Graph API for:
- Facebook Page posts
- Instagram Business posts
- Engagement tracking
- Performance summaries

⚠️ Requires Meta Developer App and Page Access Token

Usage:
    python facebook_instagram_watcher.py AI_Employee_Vault --post-facebook --message "Hello"
    python facebook_instagram_watcher.py AI_Employee_Vault --post-instagram --caption "Hello" --photo-url "http://..."
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from base_watcher import BaseWatcher


class FacebookInstagramWatcher(BaseWatcher):
    """
    Posts to Facebook and Instagram via Meta Graph API.
    """

    def __init__(self, vault_path: str, app_id: str = None, 
                 app_secret: str = None, page_id: str = None,
                 page_access_token: str = None, 
                 instagram_account_id: str = None):
        """
        Initialize the watcher.

        Args:
            vault_path: Path to Obsidian vault
            app_id: Meta App ID
            app_secret: Meta App Secret
            page_id: Facebook Page ID
            page_access_token: Page Access Token
            instagram_account_id: Instagram Business Account ID
        """
        super().__init__(vault_path, check_interval=300)
        
        self.app_id = app_id or os.getenv('META_APP_ID')
        self.app_secret = app_secret or os.getenv('META_APP_SECRET')
        self.page_id = page_id or os.getenv('META_PAGE_ID')
        self.page_access_token = page_access_token or os.getenv('META_PAGE_ACCESS_TOKEN')
        self.instagram_account_id = instagram_account_id or os.getenv('INSTAGRAM_ACCOUNT_ID')
        
        self.graph_url = 'https://graph.facebook.com/v18.0'
        
        # Folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'

    def post_to_facebook(self, message: str, photo_url: Optional[str] = None,
                        link: Optional[str] = None) -> Dict:
        """
        Post to Facebook Page.

        Args:
            message: Post message
            photo_url: Optional photo URL
            link: Optional link to share

        Returns:
            Post result dictionary
        """
        if not self.page_access_token:
            raise Exception("Facebook Page Access Token not configured")
        
        endpoint = f"{self.graph_url}/{self.page_id}/feed"
        
        params = {
            'message': message,
            'access_token': self.page_access_token
        }
        
        if photo_url:
            endpoint = f"{self.graph_url}/{self.page_id}/photos"
            params['url'] = photo_url
        
        if link:
            params['link'] = link
        
        try:
            response = requests.post(endpoint, params=params)
            result = response.json()
            
            if 'id' in result:
                self.logger.info(f"Facebook post created: {result['id']}")
                return {
                    'success': True,
                    'post_id': result['id'],
                    'platform': 'facebook'
                }
            else:
                self.logger.error(f"Facebook post failed: {result}")
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Unknown error')
                }
                
        except Exception as e:
            self.logger.error(f"Facebook post error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def post_to_instagram(self, caption: str, photo_url: str,
                         is_story: bool = False) -> Dict:
        """
        Post to Instagram Business account.

        Args:
            caption: Instagram caption
            photo_url: Photo URL (must be publicly accessible)
            is_story: Post as story (default: False)

        Returns:
            Post result dictionary
        """
        if not self.instagram_account_id or not self.page_access_token:
            raise Exception("Instagram configuration not complete")
        
        try:
            # Step 1: Create media container
            container_endpoint = f"{self.graph_url}/{self.instagram_account_id}/media"
            
            if is_story:
                params = {
                    'image_url': photo_url,
                    'media_type': 'STORIES',
                    'access_token': self.page_access_token
                }
            else:
                params = {
                    'image_url': photo_url,
                    'caption': caption,
                    'access_token': self.page_access_token
                }
            
            container_response = requests.post(container_endpoint, params=params)
            container_result = container_response.json()
            
            if 'id' not in container_result:
                return {
                    'success': False,
                    'error': container_result.get('error', {}).get('message', 'Container creation failed')
                }
            
            creation_id = container_result['id']
            
            # Step 2: Publish media
            publish_endpoint = f"{self.graph_url}/{self.instagram_account_id}/media_publish"
            publish_params = {
                'creation_id': creation_id,
                'access_token': self.page_access_token
            }
            
            publish_response = requests.post(publish_endpoint, params=publish_params)
            publish_result = publish_response.json()
            
            if 'id' in publish_result:
                self.logger.info(f"Instagram post created: {publish_result['id']}")
                return {
                    'success': True,
                    'post_id': publish_result['id'],
                    'platform': 'instagram'
                }
            else:
                return {
                    'success': False,
                    'error': publish_result.get('error', {}).get('message', 'Publish failed')
                }
                
        except Exception as e:
            self.logger.error(f"Instagram post error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_insights(self) -> Dict:
        """
        Get page/account insights.

        Returns:
            Insights dictionary
        """
        insights = {
            'facebook': {},
            'instagram': {}
        }
        
        # Facebook Page Insights
        if self.page_access_token:
            try:
                fb_insights_url = f"{self.graph_url}/{self.page_id}/insights"
                params = {
                    'metric': 'page_impressions_unique,page_engagements,page_post_engagements',
                    'period': 'day',
                    'access_token': self.page_access_token
                }
                
                response = requests.get(fb_insights_url, params=params)
                fb_data = response.json()
                
                if 'data' in fb_data:
                    insights['facebook'] = self._parse_insights(fb_data['data'])
                    
            except Exception as e:
                self.logger.error(f"Facebook insights error: {e}")
        
        # Instagram Insights
        if self.instagram_account_id and self.page_access_token:
            try:
                ig_insights_url = f"{self.graph_url}/{self.instagram_account_id}/insights"
                params = {
                    'metric': 'impressions,reach,engagement',
                    'period': 'day',
                    'access_token': self.page_access_token
                }
                
                response = requests.get(ig_insights_url, params=params)
                ig_data = response.json()
                
                if 'data' in ig_data:
                    insights['instagram'] = self._parse_insights(ig_data['data'])
                    
            except Exception as e:
                self.logger.error(f"Instagram insights error: {e}")
        
        return insights

    def _parse_insights(self, insights_data: List) -> Dict:
        """Parse insights API response."""
        parsed = {}
        for insight in insights_data:
            metric = insight.get('name', 'unknown')
            values = insight.get('values', [])
            if values:
                parsed[metric] = values[-1].get('value', 0)
        return parsed

    def create_approval_post(self, platform: str, content: Dict) -> Path:
        """
        Create approval request for social media post.

        Args:
            platform: 'facebook' or 'instagram'
            content: Post content dictionary

        Returns:
            Path to approval file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"APPROVAL_REQUIRED_{platform}_post_{timestamp}.md"
        filepath = self.pending_approval / filename
        
        content_md = f'''---
type: approval_request
action: social_media_post
platform: {platform}
created: {datetime.now().isoformat()}
status: pending
---

# {platform.title()} Post Approval Required

## Post Preview

**Platform:** {platform.title()}

**Content:**
{content.get('message', content.get('caption', ''))}

{f"**Photo URL:** {content.get('photo_url', 'N/A')}" if content.get('photo_url') else ''}
{f"**Link:** {content.get('link', 'N/A')}" if content.get('link') else ''}

## Instructions

### To Approve
1. Review the content above
2. Move this file to `Approved/` folder
3. AI will post automatically

### To Reject
1. Move this file to `Rejected/` folder
2. Add reason for rejection in notes below

## Notes

*Add rejection reason or comments here...*

---
*Generated by Facebook/Instagram Watcher v0.1*
'''
        
        filepath.write_text(content_md, encoding='utf-8')
        self.logger.info(f"Created approval file: {filepath}")
        return filepath

    def process_approved_posts(self):
        """Process approved posts from Approved folder."""
        approved_files = list(self.approved.glob('APPROVAL_REQUIRED_*_post_*.md'))
        
        for filepath in approved_files:
            content = filepath.read_text(encoding='utf-8')
            
            # Parse platform and content
            import re
            platform_match = re.search(r'platform:\s*(\w+)', content)
            platform = platform_match.group(1) if platform_match else 'facebook'
            
            # Extract content
            content_match = re.search(r'\*\*Content:\*\*\n(.*?)\n\n', content, re.DOTALL)
            message = content_match.group(1).strip() if content_match else ''
            
            # Post to platform
            if platform == 'facebook':
                result = self.post_to_facebook(message)
            elif platform == 'instagram':
                photo_match = re.search(r'\*\*Photo URL:\*\*\s*(\S+)', content)
                photo_url = photo_match.group(1) if photo_match else ''
                result = self.post_to_instagram(message, photo_url)
            else:
                result = {'success': False, 'error': f'Unknown platform: {platform}'}
            
            # Move file based on result
            if result.get('success'):
                done_path = self.done / filepath.name
                filepath.rename(done_path)
                self.logger.info(f"Post successful, moved to Done: {filepath.name}")
            else:
                self.logger.error(f"Post failed: {result.get('error')}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook/Instagram Watcher')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--post-facebook', action='store_true', help='Post to Facebook')
    parser.add_argument('--post-instagram', action='store_true', help='Post to Instagram')
    parser.add_argument('--message', type=str, help='Post message')
    parser.add_argument('--caption', type=str, help='Instagram caption')
    parser.add_argument('--photo-url', type=str, help='Photo URL')
    parser.add_argument('--link', type=str, help='Link to share')
    parser.add_argument('--create-post', action='store_true', help='Create approval post')
    parser.add_argument('--platform', type=str, default='facebook', help='Platform (facebook/instagram)')
    parser.add_argument('--insights', action='store_true', help='Get insights')
    parser.add_argument('--process-approved', action='store_true', help='Process approved posts')
    
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
    
    watcher = FacebookInstagramWatcher(str(vault_path))
    
    if args.insights:
        insights = watcher.get_insights()
        print("\n=== Social Media Insights ===\n")
        print(f"Facebook:")
        for metric, value in insights['facebook'].items():
            print(f"  {metric}: {value}")
        print(f"\nInstagram:")
        for metric, value in insights['instagram'].items():
            print(f"  {metric}: {value}")
    
    elif args.create_post:
        content = {
            'message': args.message or args.caption,
            'photo_url': args.photo_url,
            'link': args.link
        }
        filepath = watcher.create_approval_post(args.platform, content)
        print(f"[OK] Created approval file: {filepath}")
    
    elif args.post_facebook:
        if not args.message:
            print("Error: --message required for Facebook post")
            sys.exit(1)
        result = watcher.post_to_facebook(args.message, args.photo_url, args.link)
        if result['success']:
            print(f"[OK] Facebook post created: {result['post_id']}")
        else:
            print(f"[FAIL] Facebook post failed: {result['error']}")
    
    elif args.post_instagram:
        if not args.caption or not args.photo_url:
            print("Error: --caption and --photo-url required for Instagram post")
            sys.exit(1)
        result = watcher.post_to_instagram(args.caption, args.photo_url)
        if result['success']:
            print(f"[OK] Instagram post created: {result['post_id']}")
        else:
            print(f"[FAIL] Instagram post failed: {result['error']}")
    
    elif args.process_approved:
        watcher.process_approved_posts()
        print("[OK] Processed approved posts")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
