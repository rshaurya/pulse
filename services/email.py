import os
import resend
import markdown
from core.config import settings

# Initialize Resend with your API Key
resend.api_key = os.environ.get("RESEND_API_KEY")

def send_daily_digest(articles: list[dict], to_email: str, user_id: str):
    """Formats and sends the top Qdrant articles as an HTML email digest via Resend."""
    
    print(f"[EMAIL] Formatting digest for {len(articles)} articles...")
    
    # The Base URL where your FastAPI server is running (Your Vercel or Render domain in production)
    BASE_URL = os.environ.get("https://pulse-gjxl.onrender.com")
    
    if not BASE_URL or BASE_URL == "None":
        BASE_URL = "http://localhost:8000"
        
    print(f"[EMAIL] Routing feedback buttons to: {BASE_URL}")

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
                    <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&user_id={user_id}&action=explore" 
                    style="background-color: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold; margin-right: 10px;">
                    📈 I like this
                    </a>
                    <a href="{BASE_URL}/api/feedback?doc_id={doc_id}&user_id={user_id}&action=prune" 
                    style="background-color: #d73a49; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold;">
                    📉 not interested
                    </a>
                </div>
            </div>
        """
        
    html_content += """
      </body>
    </html>
    """
    
    try:
        print("[EMAIL] Connecting to Resend API...")
        r = resend.Emails.send({
            "from": "PULSE Engine <shaurya@pulse-ai.me>", # Change this to your domain later if you verify it on Resend
            "to": [to_email],
            "subject": "🧠 PULSE: Your Daily Technical Digest",
            "html": html_content
        })
        print("[EMAIL] Digest successfully dispatched to inbox!")
    except Exception as e:
        print(f"[CRITICAL ERROR] FAILED to send digest via Resend: {e}")
        raise e
    
def send_magic_link_email(to_email: str, magic_link: str):
    """Dispatches the secure passwordless login link via Resend."""
    print(f"[AUTH] Dispatching Magic Link to {to_email}...")
    
    html_content = f"""
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 10px;">
        <h2 style="color: #2c3e50; text-align: center;">Welcome to PULSE</h2>
        <p style="color: #4a5568; font-size: 16px; text-align: center;">Click the button below to securely log into your autonomous research engine. This link expires in 15 minutes.</p>
        
        <div style="text-align: center; margin-top: 30px; margin-bottom: 30px;">
            <a href="{magic_link}" style="background-color: #000000; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">
                Authenticate & Log In
            </a>
        </div>
        
        <p style="color: #a0aec0; font-size: 12px; text-align: center;">If you did not request this email, you can safely ignore it.</p>
      </body>
    </html>
    """
    
    try:
        r = resend.Emails.send({
            "from": "PULSE Auth <shaurya@pulse-ai.me>", # Change this to your domain later if you verify it on Resend
            "to": [to_email],
            "subject": "PULSE: Your Secure Login Link",
            "html": html_content
        })
        print(f"[AUTH] Successfully sent Magic Link to {to_email}")
        
    except Exception as e:
        print(f"[CRITICAL ERROR] The email function crashed: {str(e)}")