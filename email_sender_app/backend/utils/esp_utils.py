from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ESPService:
    def __init__(self):
        self.client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        
    async def send_email(self, to_email: str, subject: str, content: str, tracking_id: str) -> Dict:
        try:
            message = Mail(
                from_email=os.getenv('SENDER_EMAIL'),
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            message.custom_args = {'tracking_id': tracking_id}
            
            response = await self.client.send(message)
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'status': 'sent'
            }
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
            
    async def get_email_status(self, tracking_id: str) -> Dict:
        try:
            response = await self.client.client.stats.get(
                query_params={
                    'unique_args': {'tracking_id': tracking_id}
                }
            )
            return response.to_dict()
        except Exception as e:
            logger.error(f"Error getting email status: {str(e)}")
            return {'error': str(e)} 