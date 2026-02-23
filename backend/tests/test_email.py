import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

SENDER_EMAIL = os.getenv("SMTP_USER")
APP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = "arthurcristian.peter@gmail.com" # Where to send the test email
# --------------------------------

def test_smtp():
    print("Preparing email...")
    
    # Create a simple email
    msg = EmailMessage()
    msg['Subject'] = "Success! VacationAgent SMTP is Working"
    msg['From'] = f"Turag Test <{SENDER_EMAIL}>"
    msg['To'] = RECEIVER_EMAIL
    msg.set_content("Hello! If you are reading this, your Google SMTP credentials and App Password are working perfectly.")

    try:
        # Connect to Gmail server
        print("Connecting to smtp.gmail.com...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        
        # Secure the connection
        server.starttls() 
        
        # Log in
        print("Logging in...")
        server.login(SENDER_EMAIL, APP_PASSWORD)
        
        # Send the email
        print("Sending email...")
        server.send_message(msg)
        
        # Close connection
        server.quit()
        
        print("✅ Email sent successfully! Go check your inbox.")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication Failed: Please check that your email and App Password are correct and have no spaces.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    test_smtp()