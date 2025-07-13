from fastapi_mail import FastMail, MessageSchema
from app.core.config import mail_config
from typing import List, Dict

async def send_email(subject: str, recipients: List[str], template_name: str, template_body: Dict):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=template_body,
        subtype="html"
    )

    fm = FastMail(mail_config)
    await fm.send_message(message, template_name=template_name)
