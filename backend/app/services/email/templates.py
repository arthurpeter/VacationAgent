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
    Generates the final trip blueprint email.
    Works with or without a generated daily itinerary.
    """
    from_date = session_data.get("from_date", "TBD")
    to_date = session_data.get("to_date", "TBD")
    
    flight_html = ""
    if session_data.get("flights_url"):
        price = f"{session_data.get('flight_price', 'N/A')} {session_data.get('currency', 'EUR')}"
        flight_html = f"""
        <div style="margin-bottom: 15px; padding: 15px; background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #1e293b;">✈️ Flights (Estimated: {price})</h4>
            <a href="{session_data['flights_url']}" style="color: #3b82f6; text-decoration: none; font-size: 14px;">View & Book Flight Options &rarr;</a>
        </div>
        """

    hotel_html = ""
    if session_data.get("accomodation_url"):
        price = f"{session_data.get('accomodation_price', 'N/A')} {session_data.get('currency', 'EUR')}"
        hotel_html = f"""
        <div style="margin-bottom: 15px; padding: 15px; background: #f8fafc; border-left: 4px solid #10b981; border-radius: 4px;">
            <h4 style="margin: 0 0 5px 0; color: #1e293b;">🏨 Accommodation (Estimated: {price})</h4>
            <a href="{session_data['accomodation_url']}" style="color: #10b981; text-decoration: none; font-size: 14px;">View & Book Accomodation Options &rarr;</a>
        </div>
        """

    itinerary_html = ""
    itinerary_data = session_data.get("itinerary_data")
    
    if itinerary_data and isinstance(itinerary_data, list):
        itinerary_html = """
        <h3 style="color: #0f172a; margin-top: 30px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            📅 Your Daily Itinerary
        </h3>
        """
        for day in itinerary_data:
            day_title = day.get('title', f"Day {day.get('day', '')}")
            raw_description = day.get('description', '')
            html_description = markdown2.markdown(
                raw_description, 
                extras=["cuddled-lists", "break-on-newline"]
            )
            
            links_html = ""
            if day.get("links"):
                for link in day["links"]:
                    links_html += f"""
                    <div style="margin-top: 10px; padding: 10px; background: #e0e7ff; border-radius: 6px;">
                        <strong>{link.get('name', 'Activity')}</strong><br/>
                        <a href="{link.get('url', '#')}" style="color: #4f46e5; text-decoration: none; font-size: 13px; font-weight: bold;">
                            View Details &rarr;
                        </a>
                    </div>
                    """

            itinerary_html += f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #3b82f6; font-size: 18px;">{day_title}</h4>
                <p style="margin: 0; font-size: 14px; color: #475569; line-height: 1.6;">{html_description}</p>
                {links_html}
            </div>
            """
    else:
        itinerary_html = """
        <div style="margin-top: 30px; padding: 20px; background: #f1f5f9; border-radius: 8px; text-align: center;">
            <p style="margin: 0; color: #64748b;"><em>You haven't generated a daily itinerary yet, but your travel options are ready above!</em></p>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; padding: 20px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
            
            <div style="background-color: #0f172a; padding: 30px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Your TuRAG Vacation Blueprint 🌴</h1>
                <p style="color: #94a3b8; margin: 10px 0 0 0; font-size: 16px;">{session_data.get('origin', 'Home')} to {session_data.get('destination', 'Paradise')}</p>
            </div>

            <div style="padding: 30px 20px;">
                <p style="font-size: 16px; color: #334155; margin-top: 0;">Hi,</p>
                <p style="font-size: 16px; color: #334155;">Your trip details for <strong>{from_date}</strong> to <strong>{to_date}</strong> are ready. Here is everything we've collected for you:</p>

                <div style="margin-top: 25px;">
                    {flight_html}
                    {hotel_html}
                </div>

                {itinerary_html}

                <div style="margin-top: 40px; text-align: center;">
                    <a href="http://localhost:5173/dashboard" style="display: inline-block; background-color: #0f172a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Trip in Dashboard</a>
                </div>
            </div>

            <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; color: #94a3b8; font-size: 13px;">Safe travels,<br>The TuRAG Team</p>
            </div>
        </div>
    </body>
    </html>
    """