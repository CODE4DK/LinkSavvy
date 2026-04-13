import feedparser
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 1. SETUP ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Define the feeds LinkSavvy should monitor
# You can add The Verge, Wired, or niche industry blogs here
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/"
}

# The familiar system prompt, optimized for autonomous news generation
agent_prompt = """
You are LinkSavvy, an autonomous LinkedIn Growth Strategist.
Your current task: Read the provided news summary and write a "Hot Take" LinkedIn post.
1. DWELL TIME PROTOCOL: Prioritize "Pattern Interrupt" hooks (surprising 1st sentences). Use the "1-3-1" structure (1 sentence, 3 bullet points, 1 punchline).
2. LEXICAL DIVERSITY: Write like a confident, human professional. No AI cliches.
3. VALUE ADD: Don't just summarize the news. Provide a perspective on WHY this matters to the tech industry.
"""

# --- 2. THE HUNTER FUNCTION ---
def fetch_latest_news():
    """Scrapes the RSS feeds and returns the most recent article."""
    print("🕵️ LinkSavvy Agent: Hunting for breaking news...")
    
    # We will just grab the top article from TechCrunch for this test
    feed = feedparser.parse(RSS_FEEDS["TechCrunch"])
    
    if feed.entries:
        top_entry = feed.entries[0]
        news_data = {
            "title": top_entry.title,
            "link": top_entry.link,
            "summary": top_entry.summary,
            "published": top_entry.published
        }
        print(f"📰 Found News: {news_data['title']}")
        return news_data
    else:
        print("⚠️ No news found.")
        return None

# --- 3. THE GHOSTWRITER FUNCTION ---
def draft_linkedin_post(news_data):
    """Passes the news to Gemini to generate a LinkedIn post."""
    print("✍️ LinkSavvy Agent: Drafting LinkedIn post...")
    
    prompt = f"""
    Write a LinkedIn post about this recent news:
    Title: {news_data['title']}
    Link: {news_data['link']}
    Summary: {news_data['summary']}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=agent_prompt,
            temperature=0.7 
        )
    )
    
    return response.text

# --- 4. THE STORAGE FUNCTION ---
def save_draft_to_inbox(news_title, news_link, generated_draft):
    """Saves the draft to a local JSON file so the UI can read it later."""
    draft_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_title": news_title,
        "source_link": news_link,
        "status": "PENDING_REVIEW",
        "draft_content": generated_draft
    }
    
    # Read existing drafts (or create new list)
    drafts = []
    if os.path.exists("agent_drafts.json"):
        with open("agent_drafts.json", "r", encoding="utf-8") as f:
            drafts = json.load(f)
            
    # Append the new draft and save
    drafts.append(draft_record)
    with open("agent_drafts.json", "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=4)
        
    print("💾 LinkSavvy Agent: Draft saved to Inbox!")

# --- 5. EXECUTE THE AGENT RUN ---
if __name__ == "__main__":
    print("🚀 Initializing LinkSavvy Autonomous Agent...\n")
    
    # 1. Get the news
    latest_article = fetch_latest_news()
    
    if latest_article:
        # 2. Write the post
        draft = draft_linkedin_post(latest_article)
        
        # 3. Save to Inbox
        save_draft_to_inbox(latest_article["title"], latest_article["link"], draft)
        
        print("\n✨ Agent Run Complete. Check agent_drafts.json!")