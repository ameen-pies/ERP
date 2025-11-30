import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8050")

def send_validation_email(
    to_email: str,
    pr_id: str,
    pr_details: Dict[str, Any],
    validation_type: str,
    token: str
) -> bool:
    # Determine subject and greeting based on validation type
    if validation_type == "hierarchique":
        subject = f"🔔 Validation Hiérarchique Requise - PR {pr_id}"
        greeting = "Cher Manager,"
        validation_level = "VALIDATION HIÉRARCHIQUE"
        instructions = "En tant que responsable hiérarchique, veuillez examiner cette requête d'achat et prendre une décision."
    else:
        subject = f"💰 Validation Budgétaire Requise - PR {pr_id}"
        greeting = "Cher Responsable Financier,"
        validation_level = "VALIDATION BUDGÉTAIRE"
        instructions = "En tant que responsable financier, veuillez vérifier la disponibilité budgétaire et valider cette requête."
    
    # Build validation URLs
    approve_url = f"{BASE_URL}/pr/{pr_id}/validate?token={token}&action=approve&type={validation_type}"
    reject_url = f"{BASE_URL}/pr/{pr_id}/validate?token={token}&action=reject&type={validation_type}"
    
    # Format price
    prix = pr_details.get('prix_estime', 0)
    prix_formatted = f"{prix:,.2f} TND" if prix else "Non spécifié"
    
    # Build HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 3px solid #1E3A8A;
                margin-bottom: 25px;
            }}
            .header h1 {{
                color: #1E3A8A;
                margin: 0;
                font-size: 24px;
            }}
            .badge {{
                display: inline-block;
                background-color: #fef3c7;
                color: #92400e;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin-top: 10px;
            }}
            .pr-details {{
                background-color: #f9fafb;
                border-left: 4px solid #1E3A8A;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: 600;
                color: #6b7280;
            }}
            .detail-value {{
                color: #111827;
                text-align: right;
            }}
            .highlight {{
                background-color: #fef3c7;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: 600;
            }}
            .description {{
                background-color: #f3f4f6;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                font-style: italic;
            }}
            .button-container {{
                text-align: center;
                margin: 35px 0;
                padding: 20px;
                background-color: #f9fafb;
                border-radius: 8px;
            }}
            .button {{
                display: inline-block;
                padding: 15px 40px;
                margin: 10px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.3s;
            }}
            .approve-btn {{
                background-color: #10b981;
                color: white;
            }}
            .approve-btn:hover {{
                background-color: #059669;
            }}
            .reject-btn {{
                background-color: #ef4444;
                color: white;
            }}
            .reject-btn:hover {{
                background-color: #dc2626;
            }}
            .instructions {{
                background-color: #dbeafe;
                border-left: 4px solid #3b82f6;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 12px;
            }}
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 12px;
                margin: 15px 0;
                border-radius: 5px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 ERP Achat</h1>
                <div class="badge">{validation_level}</div>
            </div>
            
            <p>{greeting}</p>
            <p>{instructions}</p>
            
            <div class="pr-details">
                <h3 style="margin-top: 0; color: #1E3A8A;">📋 Détails de la Requête d'Achat</h3>
                
                <div class="detail-row">
                    <span class="detail-label">ID de la PR:</span>
                    <span class="detail-value"><strong>PR-{pr_id}</strong></span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Demandeur:</span>
                    <span class="detail-value">{pr_details.get('demandeur', 'N/A')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Email:</span>
                    <span class="detail-value">{pr_details.get('email_demandeur', 'N/A')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Type d'achat:</span>
                    <span class="detail-value"><span class="highlight">{pr_details.get('type_achat', 'N/A')}</span></span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Prix estimé:</span>
                    <span class="detail-value">
                        <strong style="color:#06402B; font-size:16px; margin-left:3px;">
                            {prix_formatted}
                        </strong>
                    </span>
                </div>

                
                <div class="detail-row">
                    <span class="detail-label">Quantité:</span>
                    <span class="detail-value">{pr_details.get('quantite', 'N/A')} {pr_details.get('unite', '')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Centre de coût:</span>
                    <span class="detail-value">{pr_details.get('centre_cout', 'Non spécifié')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Priorité:</span>
                    <span class="detail-value">{pr_details.get('priorite', 'Moyenne')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Délai souhaité:</span>
                    <span class="detail-value">{pr_details.get('delai_souhaite', 'Non spécifié')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Fournisseur suggéré:</span>
                    <span class="detail-value">{pr_details.get('fournisseur_suggere', 'Non spécifié')}</span>
                </div>
            </div>
            
            <div class="description">
                <strong>📝 Description détaillée:</strong><br>
                {pr_details.get('details', 'Aucune description fournie')}
            </div>
            
            {f'''<div class="description">
                <strong>💡 Justification:</strong><br>
                {pr_details.get('justification')}
            </div>''' if pr_details.get('justification') else ''}
            
            <div class="instructions">
                <strong>ℹ️ Instructions:</strong><br>
                Cliquez sur l'un des boutons ci-dessous pour valider votre décision. 
                Cette action mettra automatiquement à jour le statut de la requête d'achat dans le système.
            </div>
            
            <div class="button-container">
                <p style="margin-bottom: 20px;"><strong>Quelle est votre décision?</strong></p>
                <a href="{approve_url}" class="button approve-btn">
                    ✅ APPROUVER
                </a>
                <a href="{reject_url}" class="button reject-btn">
                    ❌ REJETER
                </a>
            </div>
            
            <div class="warning">
                ⚠️ <strong>Important:</strong> Cette action est immédiate et irréversible. 
                Assurez-vous d'avoir bien examiné tous les détails avant de cliquer.
            </div>
            
            <div class="footer">
                <p>
                    Cet email a été généré automatiquement par le système ERP Achat.<br>
                    Pour toute question, veuillez contacter le service des achats.
                </p>
                <p style="margin-top: 10px;">
                    © 2025 ERP Achat - Tous droits réservés
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create text version for email clients that don't support HTML
    text_body = f"""
    ERP ACHAT - {validation_level}
    
    {greeting}
    
    Une nouvelle requête d'achat nécessite votre validation.
    
    DÉTAILS DE LA PR:
    ==================
    ID: PR-{pr_id}
    Demandeur: {pr_details.get('demandeur', 'N/A')}
    Email: {pr_details.get('email_demandeur', 'N/A')}
    Type d'achat: {pr_details.get('type_achat', 'N/A')}
    Prix estimé: {prix_formatted}
    Quantité: {pr_details.get('quantite', 'N/A')} {pr_details.get('unite', '')}
    Centre de coût: {pr_details.get('centre_cout', 'Non spécifié')}
    Priorité: {pr_details.get('priorite', 'Moyenne')}
    Délai: {pr_details.get('delai_souhaite', 'Non spécifié')}
    Fournisseur suggéré: {pr_details.get('fournisseur_suggere', 'Non spécifié')}
    
    Description: {pr_details.get('details', 'Aucune description')}
    
    ACTIONS:
    ========
    Pour APPROUVER: {approve_url}
    Pour REJETER: {reject_url}
    
    Cliquez sur un des liens ci-dessus pour valider votre décision.
    
    ---
    ERP Achat - Email automatique
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"ERP Achat <{SMTP_USER}>"
        msg['To'] = to_email
        
        # Attach both text and HTML versions
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email de validation {validation_type} envoyé à {to_email} pour PR-{pr_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email: {e}")
        # In development, we don't want to block the workflow
        return True


def send_notification_email(
    to_email: str,
    subject: str,
    message: str,
    pr_id: Optional[str] = None
) -> bool:
    """
    Send general notification email
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Email message body
        pr_id: Optional PR ID for reference
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 3px solid #1E3A8A;
                margin-bottom: 25px;
            }}
            .header h1 {{
                color: #1E3A8A;
                margin: 0;
                font-size: 24px;
            }}
            .message-box {{
                background-color: #f9fafb;
                border-left: 4px solid #10b981;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 ERP Achat</h1>
                {f'<p style="color: #6b7280; margin-top: 10px;">PR-{pr_id}</p>' if pr_id else ''}
            </div>
            
            <div class="message-box">
                {message}
            </div>
            
            <div class="footer">
                <p>
                    Cet email a été généré automatiquement par le système ERP Achat.<br>
                    Pour toute question, veuillez contacter le service des achats.
                </p>
                <p style="margin-top: 10px;">
                    © 2025 ERP Achat - Tous droits réservés
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    ERP ACHAT - NOTIFICATION
    
    {message}
    
    ---
    ERP Achat - Email automatique
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"ERP Achat <{SMTP_USER}>"
        msg['To'] = to_email
        
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email de notification envoyé à {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de la notification: {e}")
        return True


def test_email_configuration() -> bool:
    """
    Test email configuration by sending a test email
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
        
        logger.info("✅ Configuration email valide")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration email invalide: {e}")
        return False


if __name__ == "__main__":
    # Test email configuration when running this file directly
    print("Testing email configuration...")
    if test_email_configuration():
        print("✅ Email configuration is valid!")
    else:
        print("❌ Email configuration has errors. Please check your .env file.")
