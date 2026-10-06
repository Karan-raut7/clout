import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

MAIL_FROM = os.getenv("MAIL_FROM")


async def send_email(
    to: str,
    subject: str,
    html: str
):
    params: resend.Emails.SendParams = {
        "from": MAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    return await resend.Emails.send_async(params)