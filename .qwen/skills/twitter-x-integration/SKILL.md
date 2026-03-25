---
name: twitter-x-integration
description: |
  Integrate Twitter (X) for automated tweeting and engagement tracking.
  Uses Twitter API v2 for posting tweets, threads, and tracking analytics.
  Supports text tweets, image tweets, and threaded conversations.
---

# Twitter (X) Integration

Automated tweeting and engagement tracking for Twitter/X platform.

## Overview

This integration uses Twitter API v2 to:
- Post tweets (text, images, threads)
- Track engagement (likes, retweets, replies)
- Monitor mentions and responses
- Generate performance analytics
- Schedule tweets at optimal times

## Prerequisites

### 1. Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Apply for developer account
3. Create a new project and app
4. Get API keys and tokens

### 2. Get API Credentials

- API Key (Consumer Key)
- API Secret Key (Consumer Secret)
- Access Token
- Access Token Secret
- Bearer Token

## Configuration

Create `.env` file:

```bash
# Twitter API Configuration
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Posting Settings
TWITTER_AUTO_POST=false
TWEET_SCHEDULE=09:00,13:00,17:00
MAX_TWEETS_PER_DAY=10
ENABLE_THREADS=true
```

## Usage

### Post Tweet

```bash
# Text tweet
python twitter_watcher.py AI_Employee_Vault \
  --tweet "Just completed Gold Tier of AI Employee hackathon! 🎉 #AI #Automation"

# Tweet with image
python twitter_watcher.py AI_Employee_Vault \
  --tweet "Check out our latest feature!" \
  --media-url "https://example.com/image.jpg"

# Create thread
python twitter_watcher.py AI_Employee_Vault \
  --thread "1/5 Here's how we built our AI Employee..." \
  --thread-file "thread_tweets.txt"
```

### Get Analytics

```bash
# Get tweet metrics
python twitter_watcher.py AI_Employee_Vault --analytics TWEET_ID

# Get account analytics
python twitter_watcher.py AI_Employee_Vault --account-analytics
```

### Monitor Mentions

```bash
# Check mentions
python twitter_watcher.py AI_Employee_Vault --mentions
```

## Content Templates

### Single Tweet Template

```markdown
[Hook/Attention grabber]

[Main content - keep it concise]

[Call to action or question]

#RelevantHashtags (2-3 max)
```

### Thread Template

```markdown
1/X [Hook that makes people want to read more]

2/X [Key point 1]

3/X [Key point 2]

4/X [Key point 3]

5/X [Summary + Call to action]
```

## Best Practices

| Aspect | Recommendation |
|--------|----------------|
| **Frequency** | 3-10 tweets per day |
| **Length** | 100-280 characters (optimal engagement) |
| **Hashtags** | 2-3 relevant hashtags |
| **Media** | Tweets with images get 150% more retweets |
| **Timing** | 9 AM, 1 PM, 5 PM (highest engagement) |
| **Engagement** | Reply within 2 hours |

## Approval Workflow

All tweets go through HITL approval:

1. Create tweet draft → `Pending_Approval/`
2. Human reviews → Move to `Approved/`
3. Auto-tweet → Move to `Done/`
4. Track engagement → Log to `Logs/twitter_*.json`

## Analytics Tracking

| Metric | Description |
|--------|-------------|
| **Impressions** | Times tweet was seen |
| **Engagements** | Total interactions |
| **Likes** | Heart reactions |
| **Retweets** | Shares |
| **Replies** | Comments |
| **Link Clicks** | URL clicks |
| **Profile Clicks** | Profile visits |

---

*Gold Tier Component - Personal AI Employee Hackathon*
