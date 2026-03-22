# 🚀 Gold Tier - Real Social Media Posting Test Guide

## Quick Start - Run All Tests

```bash
cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee

# Run the auto-posting test
python3 test_auto_post.py
```

## Manual Testing Steps

### Step 1: Verify Credentials

Check that credentials are loaded from `.env.gold-tier.example`:

```bash
# Twitter
echo $TWITTER_API_KEY
echo $TWITTER_ACCESS_TOKEN

# Facebook  
echo $FACEBOOK_ACCESS_TOKEN
echo $FACEBOOK_PAGE_ID

# Instagram
echo $INSTAGRAM_ACCESS_TOKEN
echo $INSTAGRAM_BUSINESS_ACCOUNT_ID
```

### Step 2: Install Dependencies

```bash
# Python dependencies
python3 -m pip install --break-system-packages tweepy httpx playwright

# Install Playwright browsers
python3 -m playwright install chromium
```

### Step 3: Test Twitter API

```bash
python3 -c "
import os
import tweepy

# Load credentials
api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Create client
client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# Post test tweet
response = client.create_tweet(text='🚀 Gold Tier Test from AI-Employee! #Hackathon')
print(f'Tweet posted: https://twitter.com/user/status/{response.data[\"id\"]}')
"
```

### Step 4: Test Facebook API

```bash
python3 -c "
import os
import httpx

access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
page_id = os.getenv('FACEBOOK_PAGE_ID')

url = f'https://graph.facebook.com/{page_id}/feed'
params = {
    'message': '🚀 Gold Tier Test from AI-Employee! #Hackathon',
    'access_token': access_token
}

response = httpx.post(url, data=params)
result = response.json()
print(f'Facebook post: https://facebook.com/{result[\"id\"]}')
"
```

### Step 5: Test Instagram API

```bash
python3 -c "
import os
import httpx

access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
business_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

# Create media
url = f'https://graph.facebook.com/v18.0/{business_id}/media'
params = {
    'image_url': 'https://picsum.photos/seed/test/1080/1080.jpg',
    'caption': '🚀 Gold Tier Test from AI-Employee! #Hackathon',
    'access_token': access_token
}

response = httpx.post(url, data=params)
creation_id = response.json()['id']

# Publish
publish_url = f'https://graph.facebook.com/v18.0/{business_id}/media_publish'
publish_params = {
    'creation_id': creation_id,
    'access_token': access_token
}

publish_response = httpx.post(publish_url, data=publish_params)
print(f'Instagram Media ID: {publish_response.json()[\"id\"]}')
"
```

### Step 6: Run Social Watcher

```bash
# Dry run first
DRY_RUN=true python3 social_watcher.py

# Real run with continuous monitoring
python3 social_watcher.py --watch
```

### Step 7: Start MCP Servers

```bash
# Twitter MCP Server (port 8087)
cd mcp/twitter-server && node src/index.js

# Facebook MCP Server (port 8085)
cd mcp/facebook-server && node src/index.js

# Instagram MCP Server (port 8086)
cd mcp/instagram-server && node src/index.js
```

### Step 8: Run Ralph Wiggum Loop

```bash
# Single cycle
python3 ralph_wiggum_loop.py

# Continuous mode
python3 ralph_wiggum_loop.py --continuous

# With Claude API
CLAUDE_API_KEY=your_key python3 ralph_wiggum_loop.py --continuous
```

## Test Results

After running tests, check:
- `test_results_api.json` - API test results
- `test_results_social_posting.json` - Full test results
- Your social media accounts for the test posts

## Troubleshooting

### Twitter API Error
- Check credentials in `.env.gold-tier.example`
- Verify Twitter Developer account is active
- Check API rate limits

### Facebook/Instagram API Error
- Verify Page access token is valid
- Check Instagram Business account is linked to Facebook Page
- Token may have expired - regenerate from Graph API Explorer

### Playwright Browser Error
```bash
python3 -m playwright install chromium
```

### MCP Server Not Starting
```bash
# Check Node.js version
node --version  # Should be 20+

# Install dependencies
cd mcp/twitter-server && npm install
```

## Expected Output

```
======================================================================
🚀 GOLD TIER - REAL AUTO-POSTING TEST
======================================================================
📅 Time: 2026-03-07T...
📝 Test Post: 🚀 Gold Tier Test - AI-Employee Project!...
======================================================================

📂 Loading environment...
✅ Environment loaded!

📌 PHASE 1: Direct API Tests
----------------------------------------------------------------------

======================================================================
🐦 TWITTER API TEST
======================================================================
✓ API Key: QwhCpUHswb...
✓ Token: 2029994576...
✓ Logged in as: @yourusername
📝 Posting tweet...
✅ Tweet posted!
🔗 https://twitter.com/user/status/1234567890

======================================================================
📘 FACEBOOK API TEST
======================================================================
✓ Token: EAAb0ZCaW9atEBQ...
✓ Page ID: 1006374785894112
📝 Posting to Facebook Page...
✅ Facebook post successful!
🔗 https://facebook.com/1006374785894112_1234567890

======================================================================
📸 INSTAGRAM API TEST
======================================================================
✓ Token: EAAb0ZCaW9atEBQ...
✓ Business ID: 1006374785894112
📝 Creating media container...
✓ Media container created: 17841405309211844
📝 Publishing...
✅ Instagram post successful!
🔗 Media ID: 17841405309211844

======================================================================
📊 API TEST SUMMARY
======================================================================
✅ PASS | Twitter API
✅ PASS | Facebook API
✅ PASS | Instagram API

📈 Results: 3/3 passed (100%)
💾 Results saved to: test_results_api.json
======================================================================

✅ SOME TESTS PASSED - Check your social media accounts!
```

## Files Created

- `test_auto_post.py` - Main test script
- `test_real_social_posting.py` - Comprehensive test script
- `run_social_tests.sh` - Bash script to run all tests
- `test_results_api.json` - Test results

## Next Steps

1. ✅ Run `python3 test_auto_post.py`
2. ✅ Check your social media accounts for test posts
3. ✅ Run `python3 social_watcher.py --watch` for continuous monitoring
4. ✅ Start MCP servers for Claude Desktop integration
5. ✅ Run Ralph Wiggum loop for autonomous operation
