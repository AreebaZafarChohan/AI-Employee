# Cross-Platform Notification Hub

## Overview
The Cross-Platform Notification Hub is a Claude Code skill that sends notifications or alerts across multiple platforms (Slack, Email, Teams, SMS) based on workflow events. It provides a unified interface for delivering messages to users through their preferred communication channels, ensuring reliable and timely delivery of important information.

## Key Features
- **Multi-Platform Support**: Send notifications to Slack, Email, Teams, and SMS from a single interface
- **Flexible Routing**: Deliver notifications based on user preferences and channel availability
- **Reliable Delivery**: Built-in retry mechanisms and fallback channels ensure message delivery
- **Rich Formatting**: Platform-specific message formatting for optimal user experience
- **User Preferences**: Respect individual user preferences for notification channels and timing

## Quick Start

1. **Configure your notification channels** in `notification_channels.json`:
```json
{
  "version": "1.0",
  "channels": {
    "slack": {
      "enabled": true,
      "workspace": "my-workspace",
      "bot_token": "${SLACK_BOT_TOKEN}",
      "default_channel": "#general"
    },
    "email": {
      "enabled": true,
      "smtp_host": "${EMAIL_SMTP_HOST}",
      "smtp_port": 587,
      "from_address": "noreply@company.com"
    },
    "msteams": {
      "enabled": true,
      "webhook_url": "${TEAMS_WEBHOOK_URL}"
    },
    "sms": {
      "enabled": true,
      "provider": "twilio",
      "account_sid": "${TWILIO_ACCOUNT_SID}",
      "auth_token": "${TWILIO_AUTH_TOKEN}"
    }
  },
  "user_preferences": {
    "default_channels": ["email", "slack"],
    "business_hours_only": false,
    "channel_priorities": {
      "critical": ["sms", "slack"],
      "normal": ["email", "slack"],
      "low": ["email"]
    }
  }
}
```

2. **Set up environment variables**:
```bash
export SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
export EMAIL_SMTP_HOST=smtp.gmail.com
export TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
export TWILIO_ACCOUNT_SID=your-twilio-account-sid
export TWILIO_AUTH_TOKEN=your-twilio-auth-token
```

3. **Start the notification hub**:
```bash
python notification_hub.py
```

4. **Send a test notification**:
```bash
curl -X POST http://localhost:8082/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from the notification hub!",
    "channels": ["email", "slack"],
    "priority": "normal",
    "recipients": ["user@example.com", "#team-channel"]
  }'
```

## Documentation
- `SKILL.md` - Full specification and implementation details
- `docs/patterns.md` - Notification patterns and best practices
- `docs/impact-checklist.md` - Impact assessment for cross-platform notifications
- `docs/gotchas.md` - Common pitfalls and troubleshooting

## Assets
- `notification_channels.json` - Configuration template for notification channels
- `notification_hub.py` - Core notification hub implementation
- `example-notification-config.json` - Example configuration file
- `MANIFEST.md` - Skill manifest

## Anti-Patterns to Avoid
- Hardcoding specific channels in notification logic
- Missing retry mechanisms for failed deliveries
- Sending too many notifications without considering user preferences
- Blocking workflow execution for notification delivery
- Ignoring platform-specific rate limits

For detailed information on configuration options, notification patterns, and advanced features, refer to `SKILL.md`.