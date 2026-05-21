import asyncio
import os
import webbrowser
from datetime import datetime

# We have to adjust the Python path so this script can import your FastAPI services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qdrant import search_documents

async def generate_email_html(articles: list, query: str) -> str:
    """Formats the Qdrant results into a clean, modern HTML email."""
    
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    
    # The CSS and Structure for a beautiful email template
    html = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h1 style="color: #18181b; margin-bottom: 5px;">PULSE Intelligence Briefing</h1>
                <p style="color: #71717a; font-size: 14px; margin-top: 0;">Generated for {date_str}</p>
                <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 20px 0;">
                <p style="color: #3f3f46; font-style: italic;">Today's Focus: {query}</p>
    """
    
    if not articles:
        html += "<p>No new intelligence found matching your criteria today.</p>"
    else:
        for item in articles:
            payload = item.payload
            text_content = payload.get('raw_text', payload.get('text', ''))
            
            # 1. Safely extract lines from our saved Qdrant payload
            lines = text_content.split('\n')
            
            # 2. Grab the Title (Line 1)
            title = lines[0].replace('Title: ', '') if len(lines) > 0 and 'Title:' in lines[0] else f"Intel ID: {item.id}"
            
            # 3. Grab the URL (Line 2)
            url = "#"
            if len(lines) > 1 and 'URL:' in lines[1]:
                url = lines[1].replace('URL: ', '').strip()
            
            html += f"""
                <div style="margin-bottom: 30px;">
                    <a href="{url}" target="_blank" style="text-decoration: none;">
                        <h2 style="color: #2563eb; font-size: 18px; margin-bottom: 10px;">{title}</h2>
                    </a>
                    
                    <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #3b82f6; color: #334155; font-size: 15px; line-height: 1.6;">
                        {payload.get('summary', '').replace(chr(10), '<br>')}
                    </div>
                    
                    <div style="margin-top: 10px;">
                        <a href="{url}" target="_blank" style="color: #3b82f6; text-decoration: none; font-size: 14px; font-weight: 600;">
                            Read Original Article &rarr;
                        </a>
                    </div>
                </div>
            """
    return html

async def main():
    print("\n=== Starting PULSE Morning Dispatcher ===")
    
    # We craft a highly specific query to pull the exact data you care about from the vector space
    target_query = "latest in artificial intelligence"
    
    # 1. Retrieve the top 3 most relevant articles
    results = await search_documents(target_query, limit=3)
    
    # 2. Build the Email
    print("[DISPATCHER] Compiling HTML briefing...")
    html_content = await generate_email_html(results, target_query)
    
    # 3. Save and Open (Simulating the SMTP send)
    output_file = os.path.join(os.path.dirname(__file__), "daily_briefing.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[SUCCESS] Briefing generated: {output_file}")
    print("=== Dispatcher Finished ===\n")
    
    # Automatically open the email in your browser
    webbrowser.open(f"file://{os.path.abspath(output_file)}")

if __name__ == "__main__":
    asyncio.run(main())