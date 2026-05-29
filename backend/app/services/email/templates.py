import markdown2

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

def get_vacation_blueprint_html(session_data: dict) -> str:
    """
    Generates a streamlined, high-end HTML cover letter informing the 
    user that their master unmodifiable document package has been attached.
    """
    from_date = session_data.get("from_date", "TBD")
    to_date = session_data.get("to_date", "TBD")
    destination = session_data.get("destination", "Your Destination")
    
    # Simple date display extraction formatting helper
    clean_from = from_date.split("T")[0] if isinstance(from_date, str) else getattr(from_date, "strftime", lambda x: "TBD")("%b %d, %Y")
    clean_to = to_date.split("T")[0] if isinstance(to_date, str) else getattr(to_date, "strftime", lambda x: "TBD")("%b %d, %Y")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 20px; margin: 0;">
        <div style="max-width: 580px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);">
            
            <div style="background-color: #0f172a; padding: 32px 24px; text-align: center;">
                <span style="font-size: 10px; font-weight: bold; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.15em; display: block; margin-bottom: 4px;">TuRAG Travel Companion</span>
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 900; tracking-tight: -0.02em;">Pack Your Bags! 🌴</h1>
                <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 14px; font-weight: 500;">{session_data.get('origin', 'Home Base')} &rarr; {destination}</p>
            </div>

            <div style="padding: 32px 24px; color: #334155; line-height: 1.6;">
                <p style="font-size: 15px; margin-top: 0; font-weight: 500;">Hi Traveler,</p>
                <p style="font-size: 14px;">Your micro-optimized itinerary manifest coordinates for <strong>{destination}</strong> are locked and fully compiled.</p>
                
                <p style="font-size: 14px;">We have attached your official, vector-grade **Master Travel Blueprint PDF** directly to this email message header. It contains your complete sequential timeline flow, arranged accommodation references, budget calculations, and flattened transit connection maps.</p>

                <div style="margin: 24px 0; padding: 16px; background-color: #f1f5f9; border-radius: 8px; font-size: 13px; color: #475569; border-left: 3px solid #64748b;">
                    📅 <strong>Travel Timeline Window:</strong> {clean_from} — {clean_to}<br/>
                    👥 <strong>Manifest Cap:</strong> {session_data.get('adults', 1)} Adult(s) {f"· {session_data.get('children')} Child(ren)" if session_data.get('children', 0) > 0 else ""}
                </div>

                <p style="font-size: 14px;">You can review dynamic updates, toggle real-time maps, or rearrange active itinerary slots at any point via your workspace browser link.</p>

                <div style="margin: 32px 0 16px; text-align: center;">
                    <a href="http://localhost:5173/dashboard" style="display: inline-block; background-color: #0f172a; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: bold; tracking-wide: 0.05em; text-transform: uppercase; transition: background-color 0.2s;">Open Active Dashboard</a>
                </div>
            </div>

            <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; color: #94a3b8; font-size: 12px; font-weight: 500;">
                    Safe travels and smooth transits,<br>
                    <strong>The TuRAG Engineering Team</strong>
                </p>
            </div>
        </div>
    </body>
    </html>
    """