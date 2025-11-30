"""
Test email configuration
Run this to verify your SMTP settings work
"""

import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

print("="*60)
print("📧 Testing Email Configuration")
print("="*60)
print()

# Check if credentials are set
print("1️⃣ Checking environment variables...")
print(f"   SMTP_SERVER: {SMTP_SERVER}")
print(f"   SMTP_PORT: {SMTP_PORT}")
print(f"   SMTP_USER: {SMTP_USER}")
print(f"   SMTP_PASSWORD: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NOT SET'}")
print()

if not SMTP_USER or not SMTP_PASSWORD:
    print("❌ ERROR: SMTP_USER or SMTP_PASSWORD not set in .env file!")
    print()
    print("Please add to your .env file:")
    print("SMTP_USER=your-email@gmail.com")
    print("SMTP_PASSWORD=your-16-char-app-password")
    exit(1)

# Test SMTP connection
print("2️⃣ Testing SMTP connection...")
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.set_debuglevel(0)  # Set to 1 for detailed debug output
    print(f"   ✅ Connected to {SMTP_SERVER}:{SMTP_PORT}")
    
    print("3️⃣ Starting TLS encryption...")
    server.starttls()
    print("   ✅ TLS started")
    
    print("4️⃣ Logging in...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("   ✅ Login successful")
    
    # Ask if user wants to send test email
    print()
    print("="*60)
    send_test = input("Do you want to send a test email? (yes/no): ").lower()
    
    if send_test in ['yes', 'y']:
        recipient = input(f"Send test email to ({SMTP_USER}): ").strip()
        if not recipient:
            recipient = SMTP_USER
        
        print()
        print(f"5️⃣ Sending test email to {recipient}...")
        
        # Create test email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🧪 Test Email from ERP Achat"
        msg['From'] = f"ERP Achat <{SMTP_USER}>"
        msg['To'] = recipient
        
        html_body = """
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <div style="background-color: #10b981; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h1>✅ Email Configuration Works!</h1>
            </div>
            <div style="margin-top: 20px; padding: 20px; background-color: #f3f4f6; border-radius: 5px;">
                <p>If you're reading this, your email configuration is working correctly!</p>
                <p><strong>SMTP Server:</strong> {}</p>
                <p><strong>From:</strong> {}</p>
                <p><strong>Status:</strong> <span style="color: #10b981; font-weight: bold;">WORKING ✓</span></p>
            </div>
            <p style="margin-top: 20px; color: #6b7280; font-size: 12px;">
                This is a test email from ERP Achat system.
            </p>
        </body>
        </html>
        """.format(SMTP_SERVER, SMTP_USER)
        
        text_body = f"""
        EMAIL CONFIGURATION TEST
        
        ✅ Your email configuration is working!
        
        SMTP Server: {SMTP_SERVER}
        From: {SMTP_USER}
        Status: WORKING
        
        ---
        ERP Achat Test Email
        """
        
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        server.send_message(msg)
        print(f"   ✅ Test email sent to {recipient}")
        print()
        print("   📬 Check your inbox (and spam folder) for the test email!")
    
    server.quit()
    print()
    print("="*60)
    print("🎉 SUCCESS! Email configuration is working correctly!")
    print("="*60)
    print()
    print("Your PR validation emails should work now.")
    print("If you still don't receive emails, check:")
    print("  1. Spam/Junk folder")
    print("  2. Email address is correct in the PR form")
    print("  3. Backend terminal for email sending logs")
    
except smtplib.SMTPAuthenticationError:
    print()
    print("❌ AUTHENTICATION FAILED!")
    print()
    print("This usually means:")
    print("  1. Wrong email or password")
    print("  2. Using regular password instead of App Password")
    print("  3. 2FA not enabled on Gmail account")
    print()
    print("Solution:")
    print("  1. Go to: https://myaccount.google.com/security")
    print("  2. Enable '2-Step Verification'")
    print("  3. Go to: https://myaccount.google.com/apppasswords")
    print("  4. Generate an App Password for 'Mail'")
    print("  5. Update SMTP_PASSWORD in .env with the 16-char password")
    
except smtplib.SMTPException as e:
    print()
    print(f"❌ SMTP ERROR: {e}")
    print()
    print("Check your SMTP settings in .env")
    
except Exception as e:
    print()
    print(f"❌ ERROR: {e}")
    print()
    print("Make sure:")
    print("  1. You have internet connection")
    print("  2. Port 587 is not blocked by firewall")
    print("  3. SMTP settings in .env are correct")