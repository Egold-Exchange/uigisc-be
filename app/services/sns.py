"""
AWS SNS/SES Email Service for verification codes and password reset.
"""
import random
import string
import traceback
from datetime import datetime, timedelta
from typing import Dict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from app.config import settings

# In-memory store for verification codes (consider Redis for production scale)
verification_codes: Dict[str, dict] = {}

# Separate store for password reset codes
password_reset_codes: Dict[str, dict] = {}


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code."""
    return ''.join(random.choices(string.digits, k=length))


def debug_config():
    """Print debug info about AWS configuration."""
    print("=" * 60)
    print("[AWS SES DEBUG] Configuration Check")
    print("=" * 60)
    print(f"  Environment: {settings.environment}")
    print(f"  AWS Access Key configured: {bool(settings.aws_access_key_id)}")
    print(f"  AWS Access Key length: {len(settings.aws_access_key_id) if settings.aws_access_key_id else 0}")
    print(f"  AWS Secret Key configured: {bool(settings.aws_secret_access_key)}")
    print(f"  AWS Region: {settings.aws_region}")
    print(f"  SES Sender Email: {settings.ses_sender_email}")
    print("=" * 60)


def get_ses_client():
    """Get boto3 SES client configured with AWS credentials."""
    return boto3.client(
        'ses',
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region
    )


async def send_verification_code_email(email: str) -> dict:
    """
    Send a verification code to the user's email using AWS SES.
    
    Returns:
        dict with 'success' boolean and 'message' or 'error' string
    """
    # Debug: Print configuration
    debug_config()
    print(f"[AWS SES DEBUG] Attempting to send verification code to: {email}")
    
    try:
        # Generate 6-digit code
        code = generate_verification_code()
        print(f"[AWS SES DEBUG] Generated code: {code}")
        
        # Store code with 10-minute expiry
        verification_codes[email.lower()] = {
            'code': code,
            'expires_at': datetime.utcnow() + timedelta(minutes=10),
            'attempts': 0
        }
        
        # Check environment
        print(f"[AWS SES DEBUG] Current environment: '{settings.environment}'")
        
        # Check if AWS is configured
        print(f"[AWS SES DEBUG] Checking AWS configuration...")
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            print(f"[ERROR] AWS credentials not configured - cannot send verification email!")
            return {
                'success': False,
                'error': 'Email service not configured. Please contact support.'
            }
        
        if not settings.ses_sender_email:
            print(f"[ERROR] SES_SENDER_EMAIL is empty or not set!")
            return {
                'success': False,
                'error': 'Email service not configured. Please contact support.'
            }
        
        print(f"[AWS SES DEBUG] Configuration OK, preparing to send email...")
        print(f"[AWS SES DEBUG] From: {settings.ses_sender_email}")
        print(f"[AWS SES DEBUG] To: {email}")
        print(f"[AWS SES DEBUG] Region: {settings.aws_region}")
        
        # Create SES client
        ses_client = get_ses_client()
        
        # Send email
        response = ses_client.send_email(
            Source=settings.ses_sender_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': 'Your UIGISC Verification Code',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"""
Your UIGISC Verification Code

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

- The UIGISC Team
                        """.strip(),
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': get_verification_html_email(code),
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"[AWS SES DEBUG] Response: {response}")
        print(f"[AWS SES DEBUG] MessageId: {response.get('MessageId')}")
        print(f"[AWS SES SUCCESS] Verification code sent to {email}")
        
        return {
            'success': True,
            'message': 'Verification code sent successfully'
        }
        
    except NoCredentialsError:
        print(f"[AWS SES ERROR] No AWS credentials found!")
        traceback.print_exc()
        return {
            'success': False,
            'error': 'AWS credentials not configured properly'
        }
    except PartialCredentialsError:
        print(f"[AWS SES ERROR] Partial AWS credentials - missing access key or secret!")
        traceback.print_exc()
        return {
            'success': False,
            'error': 'Incomplete AWS credentials'
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"[AWS SES ERROR] ClientError: {error_code}")
        print(f"[AWS SES ERROR] Message: {error_message}")
        print(f"[AWS SES ERROR] Full response: {e.response}")
        traceback.print_exc()
        return {
            'success': False,
            'error': f"AWS SES Error: {error_code} - {error_message}"
        }
    except Exception as e:
        print(f"[AWS SES ERROR] Unexpected error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }


def verify_code(email: str, code: str) -> dict:
    """
    Verify the code entered by the user.
    
    Returns:
        dict with 'valid' boolean and 'message' string
    """
    email_lower = email.lower()
    
    if email_lower not in verification_codes:
        return {
            'valid': False,
            'message': 'No verification code found. Please request a new code.'
        }
    
    stored = verification_codes[email_lower]
    
    # Check if expired
    if datetime.utcnow() > stored['expires_at']:
        del verification_codes[email_lower]
        return {
            'valid': False,
            'message': 'Verification code has expired. Please request a new code.'
        }
    
    # Check attempts (max 5 attempts)
    if stored['attempts'] >= 5:
        del verification_codes[email_lower]
        return {
            'valid': False,
            'message': 'Too many failed attempts. Please request a new code.'
        }
    
    # Verify code
    if stored['code'] != code:
        stored['attempts'] += 1
        remaining = 5 - stored['attempts']
        return {
            'valid': False,
            'message': f'Invalid code. {remaining} attempts remaining.'
        }
    
    # Success - remove the code
    del verification_codes[email_lower]
    return {
        'valid': True,
        'message': 'Email verified successfully'
    }


def is_email_verified(email: str) -> bool:
    """
    Check if the email has been verified (code no longer in store after successful verification).
    """
    return email.lower() not in verification_codes


def clear_verification_code(email: str) -> None:
    """Clear verification code for an email (e.g., after successful registration)."""
    email_lower = email.lower()
    if email_lower in verification_codes:
        del verification_codes[email_lower]


# ==================== PASSWORD RESET FUNCTIONS ====================

async def send_password_reset_code_email(email: str) -> dict:
    """
    Send a password reset code to the user's email using AWS SES.
    
    Returns:
        dict with 'success' boolean and 'message' or 'error' string
    """
    # Debug: Print configuration
    debug_config()
    print(f"[AWS SES DEBUG] Attempting to send password reset code to: {email}")
    
    try:
        # Generate 6-digit code
        code = generate_verification_code()
        print(f"[AWS SES DEBUG] Generated reset code: {code}")
        
        # Store code with 15-minute expiry (longer for password reset)
        password_reset_codes[email.lower()] = {
            'code': code,
            'expires_at': datetime.utcnow() + timedelta(minutes=15),
            'attempts': 0,
            'verified': False
        }
        
        # Check environment
        print(f"[AWS SES DEBUG] Current environment: '{settings.environment}'")
        
        # Check if AWS is configured
        if not settings.aws_access_key_id or not settings.aws_secret_access_key or not settings.ses_sender_email:
            print(f"[ERROR] AWS SES not fully configured - cannot send password reset email!")
            return {
                'success': False,
                'error': 'Email service not configured. Please contact support.'
            }
        
        print(f"[AWS SES DEBUG] Configuration OK, preparing to send password reset email...")
        
        # Create SES client
        ses_client = get_ses_client()
        
        # Send email
        response = ses_client.send_email(
            Source=settings.ses_sender_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': 'Reset Your UIGISC Password',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"""
Reset Your UIGISC Password

Your password reset code is: {code}

This code will expire in 15 minutes.

If you didn't request this password reset, please ignore this email.

- The UIGISC Team
                        """.strip(),
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': get_password_reset_html_email(code),
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"[AWS SES DEBUG] Response: {response}")
        print(f"[AWS SES SUCCESS] Password reset code sent to {email}")
        
        return {
            'success': True,
            'message': 'Password reset code sent successfully'
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"[AWS SES ERROR] ClientError: {error_code} - {error_message}")
        traceback.print_exc()
        return {
            'success': False,
            'error': f"AWS SES Error: {error_code} - {error_message}"
        }
    except Exception as e:
        print(f"[AWS SES ERROR] Unexpected error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }


def verify_password_reset_code(email: str, code: str) -> dict:
    """
    Verify the password reset code entered by the user.
    
    Returns:
        dict with 'valid' boolean and 'message' string
    """
    email_lower = email.lower()
    
    if email_lower not in password_reset_codes:
        return {
            'valid': False,
            'message': 'No password reset code found. Please request a new code.'
        }
    
    stored = password_reset_codes[email_lower]
    
    # Check if expired
    if datetime.utcnow() > stored['expires_at']:
        del password_reset_codes[email_lower]
        return {
            'valid': False,
            'message': 'Password reset code has expired. Please request a new code.'
        }
    
    # Check attempts (max 5 attempts)
    if stored['attempts'] >= 5:
        del password_reset_codes[email_lower]
        return {
            'valid': False,
            'message': 'Too many failed attempts. Please request a new code.'
        }
    
    # Verify code
    if stored['code'] != code:
        stored['attempts'] += 1
        remaining = 5 - stored['attempts']
        return {
            'valid': False,
            'message': f'Invalid code. {remaining} attempts remaining.'
        }
    
    # Success - mark as verified but don't remove yet (needed for password reset)
    stored['verified'] = True
    return {
        'valid': True,
        'message': 'Code verified successfully. You can now reset your password.'
    }


def is_reset_code_verified(email: str) -> bool:
    """
    Check if the password reset code has been verified for this email.
    """
    email_lower = email.lower()
    if email_lower not in password_reset_codes:
        return False
    
    stored = password_reset_codes[email_lower]
    
    # Check if expired
    if datetime.utcnow() > stored['expires_at']:
        del password_reset_codes[email_lower]
        return False
    
    return stored.get('verified', False)


def clear_password_reset_code(email: str) -> None:
    """Clear password reset code for an email (after successful password reset)."""
    email_lower = email.lower()
    if email_lower in password_reset_codes:
        del password_reset_codes[email_lower]


# ==================== HTML EMAIL TEMPLATES ====================

def get_verification_html_email(code: str) -> str:
    """Generate HTML email template for verification code."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #200A53;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="background: linear-gradient(135deg, #120233 0%, #1a0845 100%); border-radius: 24px; padding: 48px 40px; border: 1px solid #3e1e75; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);">
                
                <!-- Logo/Brand -->
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px;">UIGISC</h1>
                </div>
                
                <!-- Main Content -->
                <div style="text-align: center;">
                    <h2 style="color: #ffffff; font-size: 22px; margin: 0 0 16px 0; font-weight: 600;">Verify Your Email</h2>
                    <p style="color: #C2A2F9; font-size: 16px; line-height: 1.6; margin: 0 0 32px 0;">
                        Enter this code to complete your registration:
                    </p>
                    
                    <!-- Verification Code Box -->
                    <div style="background: linear-gradient(90deg, #3D08AF 0%, #432583 100%); border-radius: 16px; padding: 24px 32px; display: inline-block; margin-bottom: 32px;">
                        <span style="color: #ffffff; font-size: 36px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace;">{code}</span>
                    </div>
                    
                    <p style="color: #8B8B8B; font-size: 14px; line-height: 1.6; margin: 0;">
                        This code will expire in <strong style="color: #C2A2F9;">10 minutes</strong>.
                    </p>
                </div>
                
                <!-- Divider -->
                <div style="border-top: 1px solid #3e1e75; margin: 32px 0;"></div>
                
                <!-- Footer -->
                <div style="text-align: center;">
                    <p style="color: #6B6B8B; font-size: 12px; line-height: 1.6; margin: 0;">
                        If you didn't request this code, you can safely ignore this email.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_password_reset_html_email(code: str) -> str:
    """Generate HTML email template for password reset."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #200A53;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="background: linear-gradient(135deg, #120233 0%, #1a0845 100%); border-radius: 24px; padding: 48px 40px; border: 1px solid #3e1e75; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);">
                
                <!-- Logo/Brand -->
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px;">UIGISC</h1>
                </div>
                
                <!-- Main Content -->
                <div style="text-align: center;">
                    <h2 style="color: #ffffff; font-size: 22px; margin: 0 0 16px 0; font-weight: 600;">Reset Your Password</h2>
                    <p style="color: #C2A2F9; font-size: 16px; line-height: 1.6; margin: 0 0 32px 0;">
                        Enter this code to reset your password:
                    </p>
                    
                    <!-- Reset Code Box (Red accent to differentiate) -->
                    <div style="background: linear-gradient(90deg, #AF083D 0%, #832543 100%); border-radius: 16px; padding: 24px 32px; display: inline-block; margin-bottom: 32px;">
                        <span style="color: #ffffff; font-size: 36px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace;">{code}</span>
                    </div>
                    
                    <p style="color: #8B8B8B; font-size: 14px; line-height: 1.6; margin: 0;">
                        This code will expire in <strong style="color: #C2A2F9;">15 minutes</strong>.
                    </p>
                </div>
                
                <!-- Divider -->
                <div style="border-top: 1px solid #3e1e75; margin: 32px 0;"></div>
                
                <!-- Footer -->
                <div style="text-align: center;">
                    <p style="color: #6B6B8B; font-size: 12px; line-height: 1.6; margin: 0;">
                        If you didn't request this password reset, you can safely ignore this email.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

