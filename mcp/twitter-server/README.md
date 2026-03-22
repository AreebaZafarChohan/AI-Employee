# MCP Twitter Server

MCP server for Twitter API v2 integration.

## Features

- Publish tweets
- Publish threads (multiple tweets)
- Reply to tweets
- Retweet
- Get tweet analytics
- Search tweets

## Configuration

Set the following environment variables:

```bash
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_TIMEOUT=30000
```

## Getting Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. Generate Bearer Token (for API v2)
4. Generate API Key & Secret (OAuth 1.0a)
5. Generate Access Token & Secret

Required permissions:
- `tweet.read`
- `tweet.write`
- `users.read`
- `offline.access`

## Installation

```bash
cd mcp/twitter-server
npm install
```

## Usage

```bash
# Start server
npm start

# Development mode
npm run dev
```

## Available Tools

| Tool | Description |
|------|-------------|
| `publish_tweet` | Publish a single tweet |
| `publish_thread` | Publish a thread of tweets |
| `reply_tweet` | Reply to a tweet |
| `retweet` | Retweet a tweet |
| `get_twitter_analytics` | Get tweet analytics |
| `search_tweets` | Search for tweets |

## Example Tool Calls

### Publish Tweet

```json
{
  "tool": "publish_tweet",
  "params": {
    "content": "Excited to announce our new AI-powered features! 🚀 #AI #Innovation"
  }
}
```

### Publish Thread

```json
{
  "tool": "publish_thread",
  "params": {
    "tweets": [
      {
        "content": "🧵 Thread: 5 tips for productivity..."
      },
      {
        "content": "1️⃣ Start your day with a clear plan..."
      },
      {
        "content": "2️⃣ Use time-blocking for deep work..."
      }
    ]
  }
}
```

### Reply to Tweet

```json
{
  "tool": "reply_tweet",
  "params": {
    "tweet_id": "1234567890123456789",
    "content": "Thanks for sharing! Great insights."
  }
}
```

### Get Analytics

```json
{
  "tool": "get_twitter_analytics",
  "params": {
    "tweet_id": "1234567890123456789"
  }
}
```

### Search Tweets

```json
{
  "tool": "search_tweets",
  "params": {
    "query": "#AI from:elonmusk",
    "max_results": 10
  }
}
```

## Tweet Limits

| Type | Limit |
|------|-------|
| Tweet text | 280 characters |
| Thread | Unlimited (practical: ~25) |
| Media per tweet | 4 images or 1 video |
| Video length | 2 minutes 20 seconds |
| Search results | 100 per request |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /tweets | 200 per 15 min |
| GET /tweets/search | 300 per 15 min |
| GET /tweets/:id | 300 per 15 min |

## Testing

```bash
npm test
```
