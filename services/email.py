import smtplib
import markdown
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
        
        title = payload.get('title', 'Untitled Intelligence')
        url = payload.get('url', '#')
        
        raw_summary = payload.get('summary', 'No summary available.')
        html_summary = markdown.markdown(raw_summary)
        
        html_content += f"""
            <div style="margin-bottom: 40px; padding: 20px; border: 1px solid #e1e4e8; border-radius: 8px; background-color: #f9fbfc;">
                <h3 style="margin-top: 0;">
                    <a href="{url}" style="color: #0366d6; text-decoration: none;" target="_blank">{title}</a>
                </h3>
                
                <div style="font-size: 14px; color: #24292e; line-height: 1.6;">
                    {html_summary}
                </div>
                
                <div style="margin-top: 20px; border-top: 1px solid #e1e4e8; padding-top: 15px;">
                    <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&action=explore" 
                    style="background-color: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold; margin-right: 10px;">
                    📈 I like this. Explore more
                    </a>
                    <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&action=prune" 
                    style="background-color: #d73a49; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold;">
                    📉 Not much to my liking :(
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
        raise e