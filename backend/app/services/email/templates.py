def get_verification_email_html(verification_link: str) -> str:
    """Template for the email verification."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2b6cb0;">Welcome to TuRAG! 🌴</h2>
                <p>Hi there,</p>
                <p>Thank you for registering. Please confirm your email address to activate your account and start planning your trips.</p>
                <br/>
                <a href="{verification_link}" style="background-color: #2b6cb0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify My Email
                </a>
                <br/><br/>
                <p style="font-size: 14px;">Or copy and paste this link into your browser:</p>
                <p style="font-size: 14px; word-break: break-all; color: #555;">{verification_link}</p>
                <br/>
                <p>Cheers,<br/>The TuRAG Team</p>
            </div>
        </body>
    </html>
    """

def get_password_reset_email_html(reset_link: str) -> str:
    """Template for the password reset email."""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2b6cb0;">Reset Your Password 🔒</h2>
                <p>Hi there,</p>
                <p>We received a request to reset your password. Click the button below to choose a new one:</p>
                <br/>
                <a href="{reset_link}" style="background-color: #2b6cb0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
                <br/><br/>
                <p style="font-size: 14px;">If you didn't request this, you can safely ignore this email. Your password will remain unchanged.</p>
                <br/>
                <p style="font-size: 14px;">Or copy and paste this link into your browser:</p>
                <p style="font-size: 14px; word-break: break-all; color: #555;">{reset_link}</p>
                <br/>
                <p>Cheers,<br/>The TuRAG Team</p>
            </div>
        </body>
    </html>
    """

def get_itinerary_email_html(user_name: str, destination: str, links: dict) -> str:
    """
    Placeholder for the itinerary email.
    """
    return f"""
    <html>
        <body>
            <h2>Your Trip to {destination} is Ready! ✈️</h2>
            <p>Hi {user_name}, your AI agent has finalized your itinerary...</p>
            </body>
    </html>
    """