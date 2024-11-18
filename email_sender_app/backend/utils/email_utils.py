# utils/email_utils.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_esp_client():
    """Initialize and return SendGrid client"""
    return SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

async def send_email(
    to_email: str,
    subject: str,
    content: str,
    esp_client: SendGridAPIClient,
    tracking_id: Optional[str] = None
):
    """Send email using SendGrid with tracking"""
    try:
        message = Mail(
            from_email=os.getenv('FROM_EMAIL'),
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        # Add custom tracking ID if provided
        if tracking_id:
            message.custom_args = {'tracking_id': tracking_id}
        
        # Enable click and open tracking
        message.tracking_settings = {
            'click_tracking': {'enable': True},
            'open_tracking': {'enable': True}
        }
        
        response = await esp_client.send(message)
        return {
            'success': True,
            'message_id': response.headers.get('X-Message-Id'),
            'status_code': response.status_code
        }
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

