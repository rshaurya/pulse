import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

def send_daily_digest(articles: list[dict]):
    """Formats and sends the top Qdrant articles as an HTML email digest."""
    print(f"[EMAIL] Formatting digest for {len(articles)} articles...")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🧠 PULSE: Your Daily Technical Digest"
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = settings.USER_EMAIL
    
    # The Base URL where your FastAPI server is running (e.g., your DigitalOcean IP or localhost)
    # We need this so the feedback buttons know where to send the click data!
    BASE_URL = "http://127.0.0.1:8000" 

    html_content = """
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #2c3e50;">PULSE Knowledge Engine</h2>
        <p>Here is your curated technical reading for today.</p>
        <hr>
    """
    
    for article in articles:
        doc_id = article.get("id")
        payload = article.get("payload", {})
        
        # We use standard markdown-to-html conversion for the summary
        html_content += f"""
        <div style="margin-bottom: 30px; padding: 15px; border: 1px solid #eee; border-radius: 8px;">
            <p style="font-size: 14px; color: #555;">{payload.get('summary', 'No summary available').replace(chr(10), '<br>')}</p>
            
            <div style="margin-top: 15px;">
                <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&action=explore" 
                   style="background-color: #3498db; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; font-size: 12px; margin-right: 10px;">
                   📈 Want More Like This
                </a>
                <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&action=prune" 
                   style="background-color: #e74c3c; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; font-size: 12px;">
                   📉 Prune This Topic
                </a>
            </div>
        </div>
        """
        
    html_content += """
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        print("[EMAIL] Connecting to SMTP server...")
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        print("[EMAIL] Digest successfully dispatched to inbox!")
    except Exception as e:
        print(f"[EMAIL] FAILED to send digest: {e}")