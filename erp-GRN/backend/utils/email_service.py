"""
Email notification service for GRN validation and error notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Email configuration
EMAIL_SENDER = "ahmedbenyaflah42@gmail.com"
EMAIL_PASSWORD = "hrcm zyzj ltcl vvys"  # Should be a Gmail App Password, not regular password
RESPONSIBLE_EMAIL = "ahmedbenyaflah71@gmail.com"
# Note: Gmail requires App Passwords for SMTP authentication
# Generate one at: https://myaccount.google.com/apppasswords
# Base URL for API endpoints (update this to match your deployment)
BASE_URL = "http://localhost:8000"  # Change this to your actual API URL


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """
    Send email notification.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content (plain text)
        html_body: Optional HTML body content
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Validate email addresses
        if not to_email or not EMAIL_SENDER:
            print(f"ERROR: Invalid email addresses - To: {to_email}, From: {EMAIL_SENDER}")
            return False
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Add plain text version
        msg.attach(MIMEText(body, "plain"))
        
        # Add HTML version if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        # Send email with timeout to prevent hanging
        print(f"[EMAIL] Attempting to send email to {to_email} with subject: {subject}")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        # Enable debug output only if needed (set to 0 to disable)
        server.set_debuglevel(0)
        server.starttls()
        print(f"[EMAIL] Attempting to login with email: {EMAIL_SENDER}")
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        print("[EMAIL] Login successful, sending email...")
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        server.quit()
        print(f"[EMAIL] ✓ Email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[EMAIL] ✗ SMTP Authentication Error: {e}")
        print("[EMAIL] NOTE: Gmail requires an App Password, not your regular password.")
        print("[EMAIL] Steps to fix:")
        print("[EMAIL] 1. Go to: https://myaccount.google.com/apppasswords")
        print("[EMAIL] 2. Generate a new App Password for 'Mail'")
        print("[EMAIL] 3. Update EMAIL_PASSWORD in backend/utils/email_service.py with the App Password")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"[EMAIL] ✗ SMTP Recipients Refused: {e}")
        print(f"[EMAIL] The recipient email address {to_email} may be invalid.")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"[EMAIL] ✗ SMTP Server Disconnected: {e}")
        print("[EMAIL] The SMTP server closed the connection unexpectedly.")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] ✗ SMTP Error: {e}")
        return False
    except Exception as e:
        # Log detailed error information
        import traceback
        error_details = traceback.format_exc()
        print(f"[EMAIL] ✗ Failed to send email notification to {to_email}:")
        print(f"[EMAIL] Error type: {type(e).__name__}")
        print(f"[EMAIL] Error message: {str(e)}")
        print(f"[EMAIL] Full traceback:\n{error_details}")
        return False


def send_grn_notification_to_buyer(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    grn_lines: list[dict],
    grn_status: str,
    anomalies: Optional[list[dict]] = None,
) -> bool:
    """
    Send comprehensive GRN notification email to the buyer with all details.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        grn_lines: List of GRN line details (each with item_name, received_qty, accepted_qty, qty_ordered, quality_status, remaining_qty)
        grn_status: GRN status (registered or pending)
        anomalies: Optional list of anomalies/errors to include in the email
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"GRN Created: {grn_reference}"
    
    # Build plain text body
    plain_lines = []
    for line in grn_lines:
        plain_lines.append(
            f"- {line.get('item_name', 'Unknown')}: "
            f"Ordered: {line.get('qty_ordered', 0)}, "
            f"Received: {line.get('received_qty', 0)}, "
            f"Accepted: {line.get('accepted_qty', 0)}, "
            f"Quality: {line.get('quality_status', 'N/A').upper()}, "
            f"Remaining: {line.get('remaining_qty', 0)}"
        )
    
    plain_body = f"""
Dear Buyer,

A Goods Receipt Note (GRN) has been created for a delivery.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}
- Status: {grn_status.upper()}

Delivery Details:
{chr(10).join(plain_lines)}

Best regards,
ERP System
    """
    
    # Build HTML content
    status_color = "#28a745" if grn_status == "registered" else "#ff9800"
    status_text = "Registered" if grn_status == "registered" else "Pending"
    status_bg = "#d4edda" if grn_status == "registered" else "#fff3cd"
    status_border = "#28a745" if grn_status == "registered" else "#ffc107"
    
    lines_html = ""
    for idx, line in enumerate(grn_lines):
        quality_status = line.get('quality_status', 'pass').upper()
        quality_color = "#28a745" if quality_status == "PASS" else "#dc3545"
        quality_bg = "#d4edda" if quality_status == "PASS" else "#f8d7da"
        
        lines_html += f"""
        <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {quality_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #212529; font-size: 16px;">{line.get('item_name', 'Unknown Item')}</h3>
                <span style="background-color: {quality_bg}; color: {quality_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                    {quality_status}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px;">
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Ordered:</span>
                    <strong style="display: block; color: #212529; font-size: 14px;">{line.get('qty_ordered', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Received:</span>
                    <strong style="display: block; color: #212529; font-size: 14px;">{line.get('received_qty', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Accepted:</span>
                    <strong style="display: block; color: #28a745; font-size: 14px;">{line.get('accepted_qty', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Remaining:</span>
                    <strong style="display: block; color: #ff9800; font-size: 14px;">{line.get('remaining_qty', 0)} units</strong>
                </div>
            </div>
        </div>
        """
    
    html_content = f"""
        <p>Dear Buyer,</p>
        <p>A <strong>Goods Receipt Note (GRN)</strong> has been created for a delivery.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value" style="color: {status_color}; font-weight: bold;">{status_text}</span>
            </div>
        </div>
        
        <h3 style="color: #212529; margin-top: 30px; margin-bottom: 15px; font-size: 18px;">Delivery Details</h3>
        {lines_html}
        
        <p style="background-color: {status_bg}; padding: 15px; border-radius: 5px; border-left: 4px solid {status_border}; margin-top: 20px;">
            <strong>Status:</strong> This GRN has been <strong>{status_text.lower()}</strong>. 
            {"All items have been processed and accepted into stock." if grn_status == "registered" else "Some items require attention. Please check the details above."}
        </p>
    """
    
    # Add anomalies/errors section if there are any
    if anomalies:
        errors_html = '<h3 style="color: #dc3545; margin-top: 30px; margin-bottom: 15px; font-size: 18px;">⚠️ Issues Detected</h3>'
        for anomaly in anomalies:
            error_type = anomaly.get("issue_type", "Unknown")
            error_color = "#dc3545" if error_type == "Quality failure" else "#ff9800"
            error_bg = "#f8d7da" if error_type == "Quality failure" else "#fff3cd"
            errors_html += f"""
            <div style="background-color: {error_bg}; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {error_color};">
                <p style="margin: 0; color: {error_color}; font-weight: bold;">{error_type}</p>
                <p style="margin: 5px 0 0 0; color: #212529;">{anomaly.get('message', 'No details available')}</p>
            </div>
            """
        html_content += errors_html
        html_content += """
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-top: 20px;">
            <strong>⚠️ Note:</strong> The supplier has been notified about these issues and will receive verification instructions.
        </p>
        """
    
    html_content += """
        
        <p style="margin-top: 20px;">Please review the GRN details above.</p>
    """
    
    info_header = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    html_body = _get_html_template("GRN Created - Delivery Notification", html_content, header_color=info_header)
    
    return send_email(RESPONSIBLE_EMAIL, subject, plain_body, html_body)


def send_grn_validation_to_buyer(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
) -> bool:
    """
    Send GRN validation email to the buyer/responsible person.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"GRN Validation: {grn_reference}"
    
    plain_body = f"""
Dear Buyer,

A Goods Receipt Note (GRN) has been validated and processed.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}

The GRN has been successfully validated and the stock has been updated accordingly.

Best regards,
ERP System
    """
    
    html_content = f"""
        <p>Dear Buyer,</p>
        <p>A Goods Receipt Note (GRN) has been <strong>validated and processed</strong>.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
        </div>
        
        <p style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; color: #155724;">
            <strong>✓ Success:</strong> The GRN has been successfully validated and the stock has been updated accordingly.
        </p>
    """
    
    success_header = "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
    html_body = _get_html_template("GRN Validation Successful", html_content, header_color=success_header)
    
    return send_email(RESPONSIBLE_EMAIL, subject, plain_body, html_body)


def send_grn_validation_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    supplier_email: Optional[str] = None,
) -> bool:
    """
    Send GRN validation email to the supplier.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        supplier_email: Supplier email (defaults to responsible email if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"GRN Validation: {grn_reference}"
    
    plain_body = f"""
Dear {supplier_name},

Your Goods Receipt Note (GRN) has been validated and accepted.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}

The delivery has been validated and accepted. Thank you for your service.

Best regards,
ERP System
    """
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>Your Goods Receipt Note (GRN) has been <strong>validated and accepted</strong>.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
        </div>
        
        <p style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; color: #155724;">
            <strong>✓ Success:</strong> The delivery has been validated and accepted. Thank you for your service.
        </p>
    """
    
    success_header = "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
    html_body = _get_html_template("GRN Validation Successful", html_content, header_color=success_header)
    
    return send_email(to_email, subject, plain_body, html_body)


def send_grn_error_to_buyer(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    error_type: str,
    error_details: str,
) -> bool:
    """
    Send GRN error notification email to the buyer/responsible person.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        error_type: Type of error (Quality failure, Over-delivery, Under-delivery, etc.)
        error_details: Detailed error description
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"GRN Error: {grn_reference} - {error_type}"
    
    plain_body = f"""
Dear Buyer,

An error has been detected in the Goods Receipt Note (GRN).

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}
- Error Type: {error_type}

Error Details:
{error_details}

A dispute has been created and the PO quantities have NOT been updated. Please review and take appropriate action.

Best regards,
ERP System
    """
    
    # Format error details with line breaks
    formatted_details = error_details.replace('\n', '<br>')
    
    html_content = f"""
        <p>Dear Buyer,</p>
        <p>An <strong>error</strong> has been detected in the Goods Receipt Note (GRN).</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Error Type:</span>
                <span class="info-value" style="color: #dc3545; font-weight: bold;">{error_type}</span>
            </div>
        </div>
        
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; color: #721c24; margin: 20px 0;">
            <strong>⚠ Error Details:</strong>
            <p style="margin: 10px 0 0 0;">{formatted_details}</p>
        </div>
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
            <strong>Action Required:</strong> A dispute has been created and the PO quantities have <strong>NOT</strong> been updated. Please review and take appropriate action.
        </p>
    """
    
    error_header = "linear-gradient(135deg, #dc3545 0%, #c82333 100%)"
    html_body = _get_html_template(f"GRN Error: {error_type}", html_content, header_color=error_header)
    
    return send_email(RESPONSIBLE_EMAIL, subject, plain_body, html_body)


def send_grn_error_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    error_type: str,
    error_details: str,
    supplier_email: Optional[str] = None,
) -> bool:
    """
    Send GRN error notification email to the supplier.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        error_type: Type of error (Quality failure, Over-delivery, Under-delivery, etc.)
        error_details: Detailed error description
        supplier_email: Supplier email (defaults to responsible email if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"GRN Error: {grn_reference} - {error_type}"
    
    plain_body = f"""
Dear {supplier_name},

An issue has been detected with your Goods Receipt Note (GRN).

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}
- Error Type: {error_type}

Error Details:
{error_details}

Please review the issue and contact us to resolve it. The delivery has not been accepted into stock until this issue is resolved.

Best regards,
ERP System
    """
    
    # Format error details with line breaks
    formatted_details = error_details.replace('\n', '<br>')
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>An <strong>issue</strong> has been detected with your Goods Receipt Note (GRN).</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Error Type:</span>
                <span class="info-value" style="color: #dc3545; font-weight: bold;">{error_type}</span>
            </div>
        </div>
        
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; color: #721c24; margin: 20px 0;">
            <strong>⚠ Error Details:</strong>
            <p style="margin: 10px 0 0 0;">{formatted_details}</p>
        </div>
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
            <strong>Action Required:</strong> Please review the issue and contact us to resolve it. The delivery has <strong>not been accepted</strong> into stock until this issue is resolved.
        </p>
    """
    
    error_header = "linear-gradient(135deg, #dc3545 0%, #c82333 100%)"
    html_body = _get_html_template(f"GRN Error: {error_type}", html_content, header_color=error_header)
    
    return send_email(to_email, subject, plain_body, html_body)


def _get_html_template(
    title: str, 
    content: str, 
    button_text: Optional[str] = None, 
    button_url: Optional[str] = None,
    header_color: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    custom_buttons_html: Optional[str] = None
) -> str:
    """Generate a clean HTML email template."""
    button_html = ""
    if custom_buttons_html:
        button_html = custom_buttons_html
    elif button_text and button_url:
        button_html = f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{button_url}" style="background-color: #4CAF50; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                {button_text}
            </a>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background: {header_color};
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 30px -30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .content {{
                margin: 20px 0;
            }}
            .info-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .info-row {{
                margin: 10px 0;
                padding: 8px 0;
                border-bottom: 1px solid #e9ecef;
            }}
            .info-row:last-child {{
                border-bottom: none;
            }}
            .info-label {{
                font-weight: 600;
                color: #495057;
                display: inline-block;
                width: 140px;
            }}
            .info-value {{
                color: #212529;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e9ecef;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            a {{
                color: #667eea;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{title}</h1>
            </div>
            <div class="content">
                {content}
            </div>
            {button_html}
            <div class="footer">
                <p>This is an automated message from the ERP System.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_under_delivery_notification_to_buyer(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    item_name: str,
    qty_ordered: int,
    qty_received: int,
    shortfall: int,
    current_received: int = 0,
    total_received: int = 0,
    remaining_qty: int = 0,
) -> bool:
    """
    Send under-delivery notification email to the buyer (no dispute created).
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        item_name: Item name
        qty_ordered: Quantity ordered
        qty_received: Quantity received
        shortfall: Shortfall quantity
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"Under-Delivery Notification: {grn_reference}"
    
    plain_body = f"""
Dear Buyer,

An under-delivery has been detected in the Goods Receipt Note (GRN).

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}
- Item: {item_name}
- Quantity Ordered: {qty_ordered}
- Quantity Received: {qty_received}
- Shortfall: {shortfall} units

The received quantity has been accepted into stock. The PO remains open for the remaining quantity.

Best regards,
ERP System
    """
    
    html_content = f"""
        <p>Dear Buyer,</p>
        <p>An <strong>under-delivery</strong> has been detected in the Goods Receipt Note (GRN).</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Item:</span>
                <span class="info-value">{item_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Quantity Ordered:</span>
                <span class="info-value">{qty_ordered} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Previously Received:</span>
                <span class="info-value">{current_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Received in this GRN:</span>
                <span class="info-value">{qty_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Total Received:</span>
                <span class="info-value">{total_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Remaining Quantity:</span>
                <span class="info-value" style="color: #ff9800; font-weight: bold;">{remaining_qty} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Shortfall:</span>
                <span class="info-value" style="color: #dc3545; font-weight: bold;">{shortfall} units</span>
            </div>
        </div>
        
        <p>The received quantity has been <strong>accepted into stock</strong>. The Purchase Order remains <strong>open</strong> for the remaining <strong>{remaining_qty} unit(s)</strong>.</p>
        <p>No dispute has been created for this under-delivery. Please coordinate with the supplier for the remaining quantity.</p>
    """
    
    warning_header = "linear-gradient(135deg, #ff9800 0%, #f57c00 100%)"
    html_body = _get_html_template("Under-Delivery Notification", html_content, header_color=warning_header)
    
    return send_email(RESPONSIBLE_EMAIL, subject, plain_body, html_body)


def send_under_delivery_notification_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    item_name: str,
    qty_ordered: int,
    qty_received: int,
    shortfall: int,
    supplier_email: Optional[str] = None,
    current_received: int = 0,
    total_received: int = 0,
    remaining_qty: int = 0,
) -> bool:
    """
    Send under-delivery notification email to the supplier (no dispute created).
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        item_name: Item name
        qty_ordered: Quantity ordered
        qty_received: Quantity received
        shortfall: Shortfall quantity
        supplier_email: Supplier email (defaults to responsible email if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"Under-Delivery Notification: {grn_reference}"
    
    plain_body = f"""
Dear {supplier_name},

We have received your delivery, but there is a shortfall in the quantity.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Item: {item_name}
- Quantity Ordered: {qty_ordered}
- Quantity Received: {qty_received}
- Shortfall: {shortfall} units

The received quantity has been accepted. Please arrange to deliver the remaining {shortfall} unit(s) to complete the order.

Best regards,
ERP System
    """
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>We have received your delivery, but there is a <strong>shortfall</strong> in the quantity.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Item:</span>
                <span class="info-value">{item_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Quantity Ordered:</span>
                <span class="info-value">{qty_ordered} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Previously Received:</span>
                <span class="info-value">{current_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Received in this GRN:</span>
                <span class="info-value">{qty_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Total Received:</span>
                <span class="info-value">{total_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Remaining Quantity:</span>
                <span class="info-value" style="color: #ff9800; font-weight: bold;">{remaining_qty} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Shortfall:</span>
                <span class="info-value" style="color: #dc3545; font-weight: bold;">{shortfall} units</span>
            </div>
        </div>
        
        <p>The received quantity has been <strong>accepted</strong>. Please arrange to deliver the remaining <strong>{remaining_qty} unit(s)</strong> to complete the order.</p>
        <p>No dispute has been created. This is a notification only.</p>
    """
    
    warning_header = "linear-gradient(135deg, #ff9800 0%, #f57c00 100%)"
    html_body = _get_html_template("Under-Delivery Notification", html_content, header_color=warning_header)
    
    return send_email(to_email, subject, plain_body, html_body)


def send_over_delivery_notification_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    item_name: str,
    qty_ordered: int,
    qty_received: int,
    excess_qty: int,
    dispute_id: str,
    supplier_email: Optional[str] = None,
) -> bool:
    """
    Send over-delivery notification email to the supplier with verification button.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        item_name: Item name
        qty_ordered: Quantity ordered
        qty_received: Quantity received
        excess_qty: Excess quantity to return
        dispute_id: Dispute ID for verification
        supplier_email: Supplier email (defaults to responsible email if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"Over-Delivery: Products Returned - Verification Required: {grn_reference}"
    
    verification_url = f"{BASE_URL}/api/disputes/{dispute_id}/verify-receipt"
    
    plain_body = f"""
Dear {supplier_name},

We have received an over-delivery in your Goods Receipt Note (GRN) and have returned the excess products to you.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Item: {item_name}
- Quantity Ordered: {qty_ordered}
- Quantity Received: {qty_received}
- Excess Quantity Returned: {excess_qty} units

We have sent back {excess_qty} unit(s) of {item_name} to you. Please verify that you have received the returned products by clicking the verification link below:

{verification_url}

This will automatically resolve the over-delivery dispute.

Best regards,
ERP System
    """
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>We have received an <strong>over-delivery</strong> in your Goods Receipt Note (GRN).</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Item:</span>
                <span class="info-value">{item_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Quantity Ordered:</span>
                <span class="info-value">{qty_ordered} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Quantity Received:</span>
                <span class="info-value">{qty_received} units</span>
            </div>
            <div class="info-row">
                <span class="info-label">Excess Quantity:</span>
                <span class="info-value" style="color: #ff9800; font-weight: bold;">{excess_qty} units</span>
            </div>
        </div>
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
            <strong>Action Required:</strong> We will be returning <strong>{excess_qty} unit(s)</strong> to you. 
            Once you receive the returned quantity, please click the button below to confirm receipt. 
            This will automatically resolve the over-delivery dispute.
        </p>
    """
    
    warning_header = "linear-gradient(135deg, #ff9800 0%, #f57c00 100%)"
    html_body = _get_html_template(
        "Over-Delivery Notification - Return Required",
        html_content,
        "Verify Receipt of Returned Quantity",
        verification_url,
        header_color=warning_header
    )
    
    return send_email(to_email, subject, plain_body, html_body)


def send_grn_notification_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    grn_lines: list[dict],
    grn_status: str,
    supplier_email: Optional[str] = None,
    anomalies: Optional[list[dict]] = None,
) -> bool:
    """
    Send comprehensive GRN notification email to the supplier with all details.
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        grn_lines: List of GRN line details (each with item_name, received_qty, accepted_qty, qty_ordered, quality_status, remaining_qty)
        grn_status: GRN status (registered or pending)
        supplier_email: Supplier email (defaults to responsible email if not provided)
        anomalies: Optional list of anomalies/errors to include in the email
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"GRN Created: {grn_reference}"
    
    # Build plain text body
    plain_lines = []
    for line in grn_lines:
        plain_lines.append(
            f"- {line.get('item_name', 'Unknown')}: "
            f"Ordered: {line.get('qty_ordered', 0)}, "
            f"Received: {line.get('received_qty', 0)}, "
            f"Accepted: {line.get('accepted_qty', 0)}, "
            f"Quality: {line.get('quality_status', 'N/A').upper()}, "
            f"Remaining: {line.get('remaining_qty', 0)}"
        )
    
    plain_body = f"""
Dear {supplier_name},

A Goods Receipt Note (GRN) has been created for your delivery.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}
- Status: {grn_status.upper()}

Delivery Details:
{chr(10).join(plain_lines)}

Thank you for your delivery.

Best regards,
ERP System
    """
    
    # Build HTML content
    status_color = "#28a745" if grn_status == "registered" else "#ff9800"
    status_text = "Registered" if grn_status == "registered" else "Pending"
    status_bg = "#d4edda" if grn_status == "registered" else "#fff3cd"
    status_border = "#28a745" if grn_status == "registered" else "#ffc107"
    
    lines_html = ""
    for idx, line in enumerate(grn_lines):
        quality_status = line.get('quality_status', 'pass').upper()
        quality_color = "#28a745" if quality_status == "PASS" else "#dc3545"
        quality_bg = "#d4edda" if quality_status == "PASS" else "#f8d7da"
        
        lines_html += f"""
        <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {quality_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #212529; font-size: 16px;">{line.get('item_name', 'Unknown Item')}</h3>
                <span style="background-color: {quality_bg}; color: {quality_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                    {quality_status}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px;">
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Ordered:</span>
                    <strong style="display: block; color: #212529; font-size: 14px;">{line.get('qty_ordered', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Received:</span>
                    <strong style="display: block; color: #212529; font-size: 14px;">{line.get('received_qty', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Quantity Accepted:</span>
                    <strong style="display: block; color: #28a745; font-size: 14px;">{line.get('accepted_qty', 0)} units</strong>
                </div>
                <div>
                    <span style="color: #6c757d; font-size: 13px;">Remaining:</span>
                    <strong style="display: block; color: #ff9800; font-size: 14px;">{line.get('remaining_qty', 0)} units</strong>
                </div>
            </div>
        </div>
        """
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>A <strong>Goods Receipt Note (GRN)</strong> has been created for your delivery.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value" style="color: {status_color}; font-weight: bold;">{status_text}</span>
            </div>
        </div>
        
        <h3 style="color: #212529; margin-top: 30px; margin-bottom: 15px; font-size: 18px;">Delivery Details</h3>
        {lines_html}
        
        <p style="background-color: {status_bg}; padding: 15px; border-radius: 5px; border-left: 4px solid {status_border}; margin-top: 20px;">
            <strong>Status:</strong> This GRN has been <strong>{status_text.lower()}</strong>. 
            {"All items have been processed and accepted into stock." if grn_status == "registered" else "Some items require attention. Please check the details above."}
        </p>
    """
    
    # Add anomalies/errors section if there are any
    if anomalies:
        errors_html = '<h3 style="color: #dc3545; margin-top: 30px; margin-bottom: 15px; font-size: 18px;">⚠️ Issues Detected</h3>'
        for anomaly in anomalies:
            error_type = anomaly.get("issue_type", "Unknown")
            error_color = "#dc3545" if error_type == "Quality failure" else "#ff9800"
            error_bg = "#f8d7da" if error_type == "Quality failure" else "#fff3cd"
            errors_html += f"""
            <div style="background-color: {error_bg}; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {error_color};">
                <p style="margin: 0; color: {error_color}; font-weight: bold;">{error_type}</p>
                <p style="margin: 5px 0 0 0; color: #212529;">{anomaly.get('message', 'No details available')}</p>
            </div>
            """
        html_content += errors_html
        html_content += """
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-top: 20px;">
            <strong>⚠️ Note:</strong> A separate detailed email with verification instructions has been sent regarding these issues.
        </p>
        """
    
    html_content += """
        
        <p style="margin-top: 20px;">Thank you for your delivery. We appreciate your service.</p>
    """
    
    info_header = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    html_body = _get_html_template("GRN Created - Delivery Notification", html_content, header_color=info_header)
    
    return send_email(to_email, subject, plain_body, html_body)


def send_grn_issues_notification_to_supplier(
    grn_reference: str,
    po_number: str,
    supplier_name: str,
    dispute_details: list[dict],
    supplier_email: Optional[str] = None,
) -> bool:
    """
    Send comprehensive GRN issues notification to supplier with verification buttons.
    This email is sent when there are quality failures or over-deliveries (or both).
    
    Args:
        grn_reference: GRN reference number
        po_number: Purchase order number
        supplier_name: Supplier name
        dispute_details: List of dispute details, each with:
            - dispute_id: Dispute ID for verification
            - issue_type: "Quality failure" or "Over-delivery"
            - item_name: Item name
            - qty_received: Quantity received
            - qty_ordered: Quantity ordered
            - excess_qty: Excess quantity (for over-delivery)
            - quality_status: Quality status (for quality failure)
        supplier_email: Supplier email (defaults to responsible email if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use supplier email if provided, otherwise send to responsible email
    to_email = (supplier_email and supplier_email.strip()) or RESPONSIBLE_EMAIL
    subject = f"GRN Issues Requiring Action: {grn_reference}"
    
    # Separate issues by type
    quality_issues = [d for d in dispute_details if d.get("issue_type") == "Quality failure"]
    over_delivery_issues = [d for d in dispute_details if d.get("issue_type") == "Over-delivery"]
    
    # Build plain text body
    plain_issues = []
    items_to_return = []
    
    for issue in quality_issues:
        qty_to_return = issue.get('qty_to_return', issue.get('qty_received', 0))
        current_received = issue.get('current_received', 0)
        qty_received_this_grn = issue.get('qty_received', 0)
        plain_issues.append(
            f"Quality Failure: {issue.get('item_name', 'Unknown')} - "
            f"Previously Received: {current_received}, Received in this GRN: {qty_received_this_grn}, "
            f"Total Received: {current_received + qty_received_this_grn} units (Quality: FAIL)"
        )
        items_to_return.append(
            f"{issue.get('item_name', 'Unknown')}: {qty_to_return} units (Quality failure - all rejected)"
        )
    
    for issue in over_delivery_issues:
        qty_to_return = issue.get('qty_to_return', issue.get('excess_qty', 0))
        qty_ordered = issue.get('qty_ordered', 0)
        current_received = issue.get('current_received', 0)
        qty_received_this_grn = issue.get('qty_received', 0)
        total_received = issue.get('total_received', current_received + qty_received_this_grn)
        plain_issues.append(
            f"Over-Delivery: {issue.get('item_name', 'Unknown')} - "
            f"Ordered: {qty_ordered}, Previously Received: {current_received}, "
            f"Received in this GRN: {qty_received_this_grn}, Total Received: {total_received}, "
            f"Excess: {qty_to_return} units"
        )
        items_to_return.append(
            f"{issue.get('item_name', 'Unknown')}: {qty_to_return} units (Over-delivery)"
        )
    
    plain_body = f"""
Dear {supplier_name},

Issues have been detected with your Goods Receipt Note (GRN) that require your attention.

GRN Details:
- GRN Reference: {grn_reference}
- Purchase Order: {po_number}
- Supplier: {supplier_name}

Issues Detected:
{chr(10).join(plain_issues)}

Items That Have Been Returned:
{chr(10).join(items_to_return)}

These items have been sent back to you. Please verify receipt by clicking the verification link in the email.

Best regards,
ERP System
    """
    
    # Build HTML content
    issues_html = ""
    verification_buttons = []
    
    # Quality failures section
    if quality_issues:
        for issue in quality_issues:
            dispute_id = issue.get("dispute_id")
            item_name = issue.get("item_name", "Unknown")
            qty_received = issue.get("qty_received", 0)
            verification_url = f"{BASE_URL}/api/disputes/{dispute_id}/verify-receipt" if dispute_id else None
            
            qty_received_this_grn = issue.get("qty_received", qty_received)
            current_received = issue.get("current_received", 0)
            qty_to_return = issue.get("qty_to_return", qty_received_this_grn)
            qty_ordered = issue.get("qty_ordered", 0)
            
            issues_html += f"""
            <div style="background-color: #f8d7da; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #dc3545;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #721c24; font-size: 16px;">⚠️ Quality Failure: {item_name}</h3>
                    <span style="background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        QUALITY FAIL
                    </span>
                </div>
                <div style="margin: 10px 0;">
                    <p style="margin: 5px 0; color: #721c24;"><strong>Quantity Ordered:</strong> {qty_ordered} units</p>
                    <p style="margin: 5px 0; color: #721c24;"><strong>Previously Received:</strong> {current_received} units</p>
                    <p style="margin: 5px 0; color: #721c24;"><strong>Received in this GRN:</strong> {qty_received_this_grn} units</p>
                    <p style="margin: 5px 0; color: #721c24;"><strong>Quantity Returned:</strong> <span style="font-weight: bold; color: #dc3545;">{qty_to_return} units</span></p>
                </div>
                <p style="margin: 5px 0; color: #721c24;"><strong>Status:</strong> All <strong>{qty_to_return} unit(s)</strong> of <strong>{item_name}</strong> from this delivery have been <strong>rejected and returned to you</strong> due to quality failure. Please verify receipt below.</p>
            </div>
            """
            
            if verification_url:
                verification_buttons.append({
                    "text": f"Verify Receipt: {item_name} ({qty_to_return} units - Quality Failure)",
                    "url": verification_url,
                    "color": "#dc3545"
                })
    
    # Over-delivery section
    if over_delivery_issues:
        for issue in over_delivery_issues:
            dispute_id = issue.get("dispute_id")
            item_name = issue.get("item_name", "Unknown")
            qty_ordered = issue.get("qty_ordered", 0)
            current_received = issue.get("current_received", 0)
            qty_received_this_grn = issue.get("qty_received", 0)
            total_received = issue.get("total_received", current_received + qty_received_this_grn)
            qty_to_return = issue.get("qty_to_return", issue.get("excess_qty", 0))
            verification_url = f"{BASE_URL}/api/disputes/{dispute_id}/verify-receipt" if dispute_id else None
            
            issues_html += f"""
            <div style="background-color: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #856404; font-size: 16px;">📦 Over-Delivery: {item_name}</h3>
                    <span style="background-color: #ffc107; color: #856404; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        OVER-DELIVERY
                    </span>
                </div>
                <div style="margin: 10px 0;">
                    <p style="margin: 5px 0; color: #856404;"><strong>Quantity Ordered:</strong> {qty_ordered} units</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Previously Received:</strong> {current_received} units</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Received in this GRN:</strong> {qty_received_this_grn} units</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Total Received:</strong> {total_received} units</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Excess Quantity Returned:</strong> <span style="font-weight: bold; color: #ff9800;">{qty_to_return} units</span></p>
                </div>
                <p style="margin: 5px 0; color: #856404;"><strong>Status:</strong> <strong>{qty_to_return} unit(s)</strong> of <strong>{item_name}</strong> have been <strong>returned to you</strong> due to over-delivery. Please verify receipt below.</p>
            </div>
            """
            
            if verification_url:
                verification_buttons.append({
                    "text": f"Verify Receipt: {item_name} ({qty_to_return} units - Over-delivery)",
                    "url": verification_url,
                    "color": "#ff9800"
                })
    
    # Build verification buttons HTML
    buttons_html = ""
    if verification_buttons:
        buttons_html = '<div style="text-align: center; margin: 30px 0;">'
        for btn in verification_buttons:
            buttons_html += f"""
            <div style="margin: 15px 0;">
                <a href="{btn['url']}" style="background-color: {btn['color']}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    {btn['text']}
                </a>
            </div>
            """
        buttons_html += '</div>'
    
    # Summary of items being returned
    return_summary = ""
    if items_to_return:
        return_summary = f"""
        <div style="background-color: #e7f3ff; padding: 20px; border-radius: 5px; border-left: 4px solid #2196F3; margin: 20px 0;">
            <h3 style="margin: 0 0 15px 0; color: #0d47a1; font-size: 18px;">📋 Summary of Items Being Returned</h3>
            <ul style="margin: 0; padding-left: 20px; color: #0d47a1;">
                {''.join([f'<li style="margin: 8px 0;"><strong>{item}</strong></li>' for item in items_to_return])}
            </ul>
            <p style="margin: 15px 0 0 0; color: #0d47a1; font-weight: bold;">
                Once you receive these items, please click the verification button(s) above to confirm receipt.
            </p>
        </div>
        """
    
    html_content = f"""
        <p>Dear {supplier_name},</p>
        <p>Issues have been detected with your Goods Receipt Note (GRN) that <strong>require your attention</strong>.</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">GRN Reference:</span>
                <span class="info-value"><strong>{grn_reference}</strong></span>
            </div>
            <div class="info-row">
                <span class="info-label">Purchase Order:</span>
                <span class="info-value">{po_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Supplier:</span>
                <span class="info-value">{supplier_name}</span>
            </div>
        </div>
        
        <h3 style="color: #212529; margin-top: 30px; margin-bottom: 15px; font-size: 18px;">Issues Detected</h3>
        {issues_html}
        
        {return_summary}
        
        {buttons_html}
        
        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-top: 20px;">
            <strong>⚠️ Important:</strong> The products listed above have been <strong>sent back to you</strong>. Please verify that you have received them by clicking the verification button(s) above. 
            This will automatically resolve the dispute(s) in our system.
        </p>
    """
    
    error_header = "linear-gradient(135deg, #dc3545 0%, #c82333 100%)"
    html_body = _get_html_template("GRN Issues - Action Required", html_content, header_color=error_header)
    
    return send_email(to_email, subject, plain_body, html_body)
