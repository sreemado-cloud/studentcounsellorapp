"""
Email service for sending emails.
"""
try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    import warnings
    warnings.warn("aiosmtplib not installed. Email functionality will be disabled. Install with: pip install aiosmtplib")

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not AIOSMTPLIB_AVAILABLE:
        logger.warning(f"Email functionality disabled - aiosmtplib not installed. Would send email to {to_email} with subject: {subject}")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        message["To"] = to_email
        
        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, "plain")
            message.attach(text_part)
        
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email with timeout to prevent hanging
        import asyncio
        try:
            if settings.SMTP_USE_TLS:
                await asyncio.wait_for(
                    aiosmtplib.send(
                        message,
                        hostname=settings.SMTP_HOST,
                        port=settings.SMTP_PORT,
                        username=settings.SMTP_USER,
                        password=settings.SMTP_PASSWORD,
                        start_tls=True,
                    ),
                    timeout=15.0  # Overall timeout including connection
                )
            else:
                await asyncio.wait_for(
                    aiosmtplib.send(
                        message,
                        hostname=settings.SMTP_HOST,
                        port=settings.SMTP_PORT,
                        username=settings.SMTP_USER,
                        password=settings.SMTP_PASSWORD,
                        use_tls=False,
                    ),
                    timeout=15.0  # Overall timeout including connection
                )
        except asyncio.TimeoutError:
            logger.error(f"Email sending timed out for {to_email}")
            return False
        
        logger.info(f"Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_password_reset_email(email: str, reset_token: str, user_name: str) -> bool:
    """
    Send password reset email with reset link.
    
    Args:
        email: User's email address
        reset_token: Password reset token
        user_name: User's full name
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Password Reset Request - Student Counsellor"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password for your Student Counsellor account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                <p>Best regards,<br>Student Counsellor Team</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Hello {user_name},
    
    We received a request to reset your password for your Student Counsellor account.
    
    Click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
    
    Best regards,
    Student Counsellor Team
    """
    
    return await send_email(email, subject, html_body, text_body)


async def send_student_registration_notification(
    admin_email: str,
    student_name: str,
    student_email: str,
    institution_name: str
) -> bool:
    """
    Send notification email to admin when a student registers.
    
    Args:
        admin_email: Admin's email address
        student_name: Student's full name
        student_email: Student's email address
        institution_name: Institution name
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    admin_url = f"{settings.FRONTEND_URL}/admin"
    
    subject = f"New Student Registration - {student_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .info-box {{ background: #e0e7ff; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>New Student Registration</h1>
            </div>
            <div class="content">
                <p>Hello Admin,</p>
                <p>A new student has registered and is awaiting your approval:</p>
                <div class="info-box">
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Email:</strong> {student_email}</p>
                    <p><strong>Institution:</strong> {institution_name}</p>
                </div>
                <p>Please review and approve or reject the student's registration:</p>
                <p style="text-align: center;">
                    <a href="{admin_url}" class="button">Review Registration</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{admin_url}</p>
                <p>Best regards,<br>Student Counsellor System</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Hello Admin,
    
    A new student has registered and is awaiting your approval:
    
    Student Name: {student_name}
    Email: {student_email}
    Institution: {institution_name}
    
    Please review and approve or reject the student's registration at:
    {admin_url}
    
    Best regards,
    Student Counsellor System
    """
    
    return await send_email(admin_email, subject, html_body, text_body)
