import logging

logger = logging.getLogger("gold_tier")


class EmailService:
    """Placeholder for SMTP/SendGrid integration."""
    def send(self, to: str, subject: str, body: str):
        logger.info(f"[EMAIL] To: {to}, Subject: {subject}")
