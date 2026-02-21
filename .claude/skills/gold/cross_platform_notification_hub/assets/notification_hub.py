#!/usr/bin/env python3
"""
Cross-Platform Notification Hub

A Python script that implements a cross-platform notification hub to send 
notifications or alerts across multiple platforms (Slack, Email, Teams, SMS) 
based on workflow events.
"""

import asyncio
import json
import logging
import os
import smtplib
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiohttp
import redis
from jinja2 import Template


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_hub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.rate_limit = config.get('rate_limit', {})
    
    @abstractmethod
    async def send(self, message: Dict[str, Any], recipient: str) -> bool:
        """Send a notification to the channel."""
        pass


class SlackChannel(NotificationChannel):
    """Slack notification channel implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = os.getenv('SLACK_BOT_TOKEN', config.get('bot_token', ''))
        self.default_channel = config.get('default_channel', '#general')
        self.base_url = 'https://slack.com/api/chat.postMessage'
    
    async def send(self, message: Dict[str, Any], recipient: str = None) -> bool:
        if not self.enabled:
            logger.info("Slack channel is disabled")
            return False
        
        if not recipient:
            recipient = self.default_channel
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Format message using template
        template_str = self.config['message_format']['template']
        template = Template(template_str)
        formatted_message = template.render(message=message)
        
        payload = {
            'channel': recipient,
            'text': formatted_message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    result = await response.json()
                    success = result.get('ok', False)
                    if not success:
                        logger.error(f"Slack API error: {result.get('error', 'Unknown error')}")
                    return success
        except Exception as e:
            logger.error(f"Error sending to Slack: {str(e)}")
            return False


class EmailChannel(NotificationChannel):
    """Email notification channel implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        smtp_config = config['smtp']
        self.smtp_host = os.getenv('EMAIL_SMTP_HOST', smtp_config['host'])
        self.smtp_port = smtp_config['port']
        self.smtp_username = os.getenv('EMAIL_SMTP_USER', smtp_config['username'])
        self.smtp_password = os.getenv('EMAIL_SMTP_PASSWORD', smtp_config['password'])
        self.use_tls = smtp_config.get('use_tls', True)
        self.from_address = os.getenv('EMAIL_FROM_ADDRESS', config['from_address'])
    
    async def send(self, message: Dict[str, Any], recipient: str) -> bool:
        if not self.enabled:
            logger.info("Email channel is disabled")
            return False
        
        # Format message using templates
        subject_template = Template(self.config['message_format']['subject_template'])
        html_template = Template(self.config['message_format']['html_template'])
        text_template = Template(self.config['message_format']['text_template'])
        
        subject = subject_template.render(message=message)
        html_content = html_template.render(message=message)
        text_content = text_template.render(message=message)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_address
        msg['To'] = recipient
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Create SMTP session
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.use_tls:
                server.starttls(context=context)
            
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.from_address, recipient, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {str(e)}")
            return False


class TeamsChannel(NotificationChannel):
    """Microsoft Teams notification channel implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = os.getenv('TEAMS_WEBHOOK_URL', config.get('webhook_url', ''))
        # Teams message card template
        self.template = config['message_format']['template']
    
    async def send(self, message: Dict[str, Any], recipient: str = None) -> bool:
        if not self.enabled:
            logger.info("Teams channel is disabled")
            return False
        
        # Use webhook URL directly, recipient is ignored for Teams webhooks
        webhook_url = self.webhook_url
        
        # Format the message card template
        formatted_template = json.dumps(self.template).replace('{{message.', '{')
        template_obj = Template(formatted_template)
        formatted_message = template_obj.render(
            title=message.get('title', ''),
            subtitle=message.get('subtitle', ''),
            content=message.get('content', ''),
            link=message.get('link', ''),
            color=message.get('color', '0078d7')
        )
        
        payload = json.loads(formatted_message)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Teams notification sent successfully")
                        return True
                    else:
                        logger.error(f"Teams API error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending to Teams: {str(e)}")
            return False


class SMSChannel(NotificationChannel):
    """SMS notification channel implementation using Twilio."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider = config.get('provider', 'twilio')
        creds = config['credentials']
        self.account_sid = os.getenv('SMS_TWILIO_ACCOUNT_SID', creds['account_sid'])
        self.auth_token = os.getenv('SMS_TWILIO_AUTH_TOKEN', creds['auth_token'])
        self.from_number = os.getenv('SMS_FROM_NUMBER', config['from_number'])
        self.api_base_url = 'https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json'
    
    async def send(self, message: Dict[str, Any], recipient: str) -> bool:
        if not self.enabled:
            logger.info("SMS channel is disabled")
            return False
        
        # Format message using template
        template_str = self.config['message_format']['template']
        template = Template(template_str)
        formatted_message = template.render(message=message)
        
        # Truncate if too long
        max_len = self.config['message_format'].get('max_length', 160)
        truncate_indicator = self.config['message_format'].get('truncate_indicator', '...')
        
        if len(formatted_message) > max_len:
            formatted_message = formatted_message[:max_len - len(truncate_indicator)] + truncate_indicator
        
        # Prepare payload
        payload = {
            'From': self.from_number,
            'To': recipient,
            'Body': formatted_message
        }
        
        try:
            # Encode payload for form submission
            from urllib.parse import urlencode
            encoded_payload = urlencode(payload)
            
            api_url = self.api_base_url.format(self.account_sid)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    data=encoded_payload,
                    auth=aiohttp.BasicAuth(self.account_sid, self.auth_token),
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    if response.status == 201:  # Created
                        logger.info(f"SMS sent successfully to {recipient}")
                        return True
                    else:
                        logger.error(f"Twilio API error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending SMS to {recipient}: {str(e)}")
            return False


class PreferenceStore(ABC):
    """Abstract base class for user preference storage."""
    
    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences for notifications."""
        pass


class RedisPreferenceStore(PreferenceStore):
    """Redis implementation for user preferences."""
    
    def __init__(self, redis_url: str, namespace: str = "notification_preferences"):
        self.redis_client = redis.from_url(redis_url)
        self.namespace = namespace
    
    def _get_key(self, user_id: str) -> str:
        return f"{self.namespace}:{user_id}"
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        key = self._get_key(user_id)
        pref_json = self.redis_client.get(key)
        if pref_json:
            return json.loads(pref_json.decode('utf-8'))
        return {}


class InMemoryPreferenceStore(PreferenceStore):
    """In-memory implementation for user preferences (for testing)."""
    
    def __init__(self):
        self.preferences = {}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        return self.preferences.get(user_id, {})


class NotificationHub:
    """Main class for the cross-platform notification hub."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.channels = {}
        self.preference_store = None
        self.delivery_rules = {}
        self.session = None
        self.running = False
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load notification configuration from the configuration file."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize channels
        channel_configs = config.get('channels', {})
        
        if 'slack' in channel_configs:
            self.channels['slack'] = SlackChannel(channel_configs['slack'])
        
        if 'email' in channel_configs:
            self.channels['email'] = EmailChannel(channel_configs['email'])
        
        if 'msteams' in channel_configs:
            self.channels['msteams'] = TeamsChannel(channel_configs['msteams'])
        
        if 'sms' in channel_configs:
            self.channels['sms'] = SMSChannel(channel_configs['sms'])
        
        # Initialize preference store
        pref_config = config.get('user_preferences', {})
        store_type = pref_config.get('store_type', 'memory')
        
        if store_type == 'redis':
            redis_url = os.getenv('NOTIFICATION_PREFERENCES_REDIS_URL', 
                                  pref_config.get('redis_config', {}).get('url', 'redis://localhost:6379'))
            self.preference_store = RedisPreferenceStore(redis_url)
        else:
            self.preference_store = InMemoryPreferenceStore()
        
        # Load delivery rules
        self.delivery_rules = config.get('delivery_rules', {})
        
        logger.info(f"Loaded configuration with {len(self.channels)} channels")
    
    async def initialize(self):
        """Initialize the notification hub."""
        self.session = aiohttp.ClientSession()
        logger.info("Notification Hub initialized")
    
    async def close(self):
        """Close the notification hub and clean up resources."""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("Notification Hub closed")
    
    async def send_notification(
        self, 
        message: Dict[str, Any], 
        channels: List[str] = None, 
        recipients: Dict[str, str] = None,
        user_id: str = None,
        priority: str = None
    ) -> Dict[str, bool]:
        """
        Send a notification to specified channels.
        
        Args:
            message: The message to send
            channels: List of channel names to send to (if None, uses user preferences)
            recipients: Dictionary mapping channel names to recipient identifiers
            user_id: User ID to get preferences for (if channels is None)
            priority: Priority level for the message
        
        Returns:
            Dictionary mapping channel names to success status
        """
        if not channels:
            # Get channels from user preferences
            if user_id:
                user_prefs = await self.preference_store.get_user_preferences(user_id)
                channels = user_prefs.get('channels', ['email'])
            else:
                # Use default channels
                default_channels = self.delivery_rules.get('default_channels', ['email'])
                channels = default_channels
        
        if not priority:
            priority = message.get('priority', 'normal')
        
        # Get channels based on priority if not explicitly provided
        if len(channels) == 0:
            priority_config = self.delivery_rules.get('priorities', {}).get(priority, {})
            channels = priority_config.get('channels', ['email'])
        
        # Get recipients if not provided
        if not recipients:
            recipients = {}
        
        results = {}
        
        # Send to each channel
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Channel {channel_name} not configured")
                results[channel_name] = False
                continue
            
            channel = self.channels[channel_name]
            
            # Determine recipient for this channel
            recipient = recipients.get(channel_name)
            if not recipient and user_id:
                # Try to get recipient from user preferences
                user_prefs = await self.preference_store.get_user_preferences(user_id)
                recipient = user_prefs.get(f'{channel_name}_recipient')
            
            # Send the notification
            success = await channel.send(message, recipient)
            results[channel_name] = success
            
            if success:
                logger.info(f"Notification sent successfully via {channel_name}")
            else:
                logger.error(f"Failed to send notification via {channel_name}")
        
        return results
    
    async def send_priority_notification(
        self, 
        message: Dict[str, Any], 
        priority: str = 'normal',
        user_id: str = None
    ) -> Dict[str, bool]:
        """
        Send a notification based on priority level which determines channels.
        
        Args:
            message: The message to send
            priority: Priority level ('critical', 'high', 'normal', 'low')
            user_id: User ID to get preferences for
        
        Returns:
            Dictionary mapping channel names to success status
        """
        priority_config = self.delivery_rules.get('priorities', {}).get(priority, {})
        channels = priority_config.get('channels', ['email'])
        
        # Override message priority
        message['priority'] = priority
        
        return await self.send_notification(message, channels, user_id=user_id, priority=priority)


class NotificationServer:
    """HTTP server for receiving notification requests."""
    
    def __init__(self, hub: NotificationHub, port: int = 8082):
        self.hub = hub
        self.port = port
    
    async def handle_notify(self, request):
        """Handle incoming notification requests."""
        try:
            data = await request.json()
            
            message = data.get('message', {})
            channels = data.get('channels')
            recipients = data.get('recipients', {})
            user_id = data.get('user_id')
            priority = data.get('priority', 'normal')
            
            results = await self.hub.send_notification(
                message=message,
                channels=channels,
                recipients=recipients,
                user_id=user_id,
                priority=priority
            )
            
            return aiohttp.web.json_response({
                'success': True,
                'results': results
            })
        except Exception as e:
            logger.error(f"Error handling notification request: {str(e)}")
            return aiohttp.web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def start_server(self):
        """Start the HTTP server."""
        app = aiohttp.web.Application()
        app.router.add_post('/notify', self.handle_notify)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        
        site = aiohttp.web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"Notification server started on port {self.port}")
        
        # Keep the server running
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()


async def main():
    """Main entry point for the notification hub."""
    # Default paths
    config_path = os.getenv("NOTIFICATION_HUB_CONFIG_PATH", "./assets/notification_channels.json")
    
    # Create notification hub
    hub = NotificationHub(config_path)
    await hub.initialize()
    
    # Create and start server
    server = NotificationServer(hub)
    
    try:
        # Run the server in the background
        server_task = asyncio.create_task(server.start_server())
        
        # Send some test notifications
        test_message = {
            "title": "Test Notification",
            "content": "This is a test notification from the Cross-Platform Notification Hub",
            "link": "https://example.com/test",
            "priority": "normal",
            "color": "0078d7"
        }
        
        # Test sending to specific channels
        logger.info("Sending test notification to all configured channels...")
        results = await hub.send_notification(
            message=test_message,
            channels=['email'],  # Specify channels to test
            recipients={
                'email': 'test@example.com',  # Replace with actual email for real testing
                'slack': '#test-channel',     # Replace with actual channel for real testing
            }
        )
        logger.info(f"Test notification results: {results}")
        
        # Test sending with priority
        critical_message = {
            "title": "Critical Alert",
            "content": "This is a critical system alert requiring immediate attention",
            "link": "https://example.com/alert",
            "priority": "critical",
            "color": "ff0000"
        }
        
        logger.info("Sending critical notification based on priority...")
        priority_results = await hub.send_priority_notification(
            message=critical_message,
            priority='critical'
        )
        logger.info(f"Critical notification results: {priority_results}")
        
        # Keep running for demonstration
        await asyncio.sleep(30)  # Run for 30 seconds for demo
        
        # Cancel the server task
        server_task.cancel()
        await server_task
        
    except KeyboardInterrupt:
        logger.info("Shutting down notification hub...")
        await hub.close()
    except Exception as e:
        logger.error(f"Error in notification hub: {str(e)}")
        await hub.close()


if __name__ == "__main__":
    asyncio.run(main())