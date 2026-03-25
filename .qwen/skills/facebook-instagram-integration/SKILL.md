---
name: facebook-instagram-integration
description: |
  Integrate Facebook and Instagram for automated posting and engagement tracking.
  Uses Meta Graph API for cross-platform posting to Facebook Pages and Instagram
  Business accounts. Supports image posts, video posts, and stories.
---

# Facebook & Instagram Integration

Automated posting and engagement tracking for Meta platforms.

## Overview

This integration uses the Meta Graph API to:
- Post updates to Facebook Pages
- Post to Instagram Business accounts
- Track engagement (likes, comments, shares)
- Generate performance summaries
- Schedule posts across platforms

## Prerequisites

### 1. Meta Developer Account

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a developer account
3. Create a new app (Business type)

### 2. Facebook Page

- Must have admin access to the Facebook Page
- Page must be published (not draft)

### 3. Instagram Business Account

- Convert to Business or Creator account
- Connect Instagram to Facebook Page
- Get Instagram Business account ID

### 4. Get Access Tokens

```bash
# Page Access Token
https://graph.facebook.com/v18.0/{page-id}?fields=access_token

# Instagram Account ID
https://graph.facebook.com/v18.0/{page-id}?fields=instagram_business_account
```

## Configuration

Create `.env` file:

```bash
# Facebook/Instagram Configuration
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_PAGE_ID=your_page_id
META_PAGE_ACCESS_TOKEN=your_page_access_token
INSTAGRAM_ACCOUNT_ID=your_ig_business_account_id

# Posting Settings
FB_AUTO_POST=false
IG_AUTO_POST=false
POST_SCHEDULE=09:00,15:00,18:00
MAX_POSTS_PER_DAY=5
```

## Usage

### Post to Facebook

```bash
# Text post
python facebook_instagram_watcher.py AI_Employee_Vault \
  --post-facebook \
  --message "Exciting news! Our AI Employee just reached Gold Tier!"

# Photo post
python facebook_instagram_watcher.py AI_Employee_Vault \
  --post-facebook \
  --message "Check out our latest feature" \
  --photo-url "https://example.com/image.jpg"

# With approval workflow
python facebook_instagram_watcher.py AI_Employee_Vault \
  --create-post --platform facebook \
  --message "New product launch!"
```

### Post to Instagram

```bash
# Photo post
python facebook_instagram_watcher.py AI_Employee_Vault \
  --post-instagram \
  --caption "Gold Tier unlocked! 🎉 #AI #Automation" \
  --photo-url "https://example.com/image.jpg"

# Story post
python facebook_instagram_watcher.py AI_Employee_Vault \
  --post-instagram-story \
  --photo-url "https://example.com/story.jpg"
```

### Get Insights

```bash
# Get page insights
python facebook_instagram_watcher.py AI_Employee_Vault --insights

# Get post performance
python facebook_instagram_watcher.py AI_Employee_Vault --post-insights POST_ID
```

## Content Templates

### Facebook Post Template

```markdown
🎯 **Business Update**

[Your message here]

Key highlights:
✅ Point 1
✅ Point 2
✅ Point 3

Learn more: [LINK]

#Hashtag1 #Hashtag2
```

### Instagram Post Template

```markdown
[Eye-catching caption]

[Main message - keep it concise]

[Call to action]

#Relevant #Hashtags #Here
```

## Approval Workflow

All posts go through HITL approval:

1. Create post draft → `Pending_Approval/`
2. Human reviews → Move to `Approved/`
3. Auto-post → Move to `Done/`

## Engagement Tracking

| Metric | Description |
|--------|-------------|
| **Reach** | Unique users who saw post |
| **Impressions** | Total times post was seen |
| **Engagement** | Likes + Comments + Shares |
| **Click-through** | Link clicks |
| **Video Views** | 3-second video views |

## Best Practices

| Platform | Best Practices |
|----------|----------------|
| **Facebook** | Post 1-2x/day, use images, ask questions |
| **Instagram** | Post 1x/day, use 5-10 hashtags, stories daily |
| **Timing** | 9 AM, 3 PM, 6 PM (highest engagement) |
| **Content** | 80% value, 20% promotion |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Token expired | Regenerate Page Access Token |
| Permission denied | Check app permissions in Meta Dashboard |
| Post failed | Verify image URL is publicly accessible |
| Rate limit | Wait 1 hour, reduce posting frequency |

---

*Gold Tier Component - Personal AI Employee Hackathon*
