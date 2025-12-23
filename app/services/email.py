from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


async def send_verification_email(email: str, token: str, subdomain: str) -> bool:
    """
    Send verification email to user.
    
    Note: This is a placeholder implementation. Configure SMTP settings
    or integrate with email service (SendGrid, Mailgun, etc.) when ready.
    """
    if settings.environment == "development":
        # In development, just log the verification link
        verification_link = f"{settings.frontend_url}/verify-email?token={token}"
        print(f"[DEV] Verification email for {email}")
        print(f"[DEV] Verification link: {verification_link}")
        return True
    
    # Production email sending
    try:
        if not settings.smtp_user or not settings.smtp_password:
            print(f"[WARNING] SMTP not configured. Verification token for {email}: {token}")
            return True
        
        verification_link = f"{settings.frontend_url}/verify-email?token={token}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify your UIGISC account"
        message["From"] = settings.email_from
        message["To"] = email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #200A53; color: white; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #120233; border-radius: 20px; padding: 40px; border: 1px solid #3e1e75;">
                <h1 style="color: white; margin-bottom: 20px;">Welcome to UIGISC!</h1>
                <p style="color: #C2A2F9; font-size: 16px; line-height: 1.6;">
                    Thank you for registering your promo page. Your subdomain <strong>{subdomain}.uigisc.com</strong> is almost ready!
                </p>
                <p style="color: #C2A2F9; font-size: 16px; line-height: 1.6;">
                    Please click the button below to verify your email address:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="background: linear-gradient(90deg, #3D08AF, #432583); color: white; padding: 15px 40px; text-decoration: none; border-radius: 14px; font-size: 16px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                <p style="color: #8B8B8B; font-size: 12px;">
                    If you didn't create this account, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to UIGISC!
        
        Thank you for registering your promo page. Your subdomain {subdomain}.uigisc.com is almost ready!
        
        Please verify your email by clicking this link:
        {verification_link}
        
        If you didn't create this account, you can safely ignore this email.
        """
        
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


async def send_welcome_email(email: str, subdomain: str) -> bool:
    """Send welcome email after verification."""
    if settings.environment == "development":
        print(f"[DEV] Welcome email sent to {email} for subdomain {subdomain}")
        return True
    
    # TODO: Implement production welcome email
    return True
