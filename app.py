import streamlit as st
import os
import re  # NEW: Python's Regular Expression library
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tools import scrape_linkedin_url, extract_text_from_pdf, chunk_text, create_pdf_carousel
from memory import save_to_memory, recall_from_memory, get_all_memories, wipe_memory, get_memory_analytics, get_memory_details, delete_memory
import json
import requests
import urllib.parse

# --- 1. SETUP & CONFIG ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="LinkSavvy: LinkedIn Assistant", layout="wide", initial_sidebar_state="expanded")

# --- 1.6 USER AUTHENTICATION (OAuth 2.0 via LinkedIn) ---
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Set up the session states
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==========================================
# PART 2: THE LOGIN SCREEN 
# ==========================================
if not st.session_state.authenticated:
    
    st.markdown("<h1 style='text-align: center; color: #0a66c2;'>🔗 LinkSavvy</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sign in to continue</h3>", unsafe_allow_html=True)
    
    # 1. Check if LinkedIn redirected back with an authorization code
    query_params = st.query_params
    if "code" in query_params:
        auth_code = query_params["code"]
        
        # 2. Exchange the authorization code for an Access Token
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET
        }
        
        with st.spinner("Authenticating with LinkedIn..."):
            token_response = requests.post(TOKEN_URL, data=token_data)
            
            if token_response.status_code == 200:
                access_token = token_response.json().get("access_token")
                
                # 3. Use the Access Token to get User Profile Info (Name & Email)
                headers = {"Authorization": f"Bearer {access_token}"}
                user_info_response = requests.get(USERINFO_URL, headers=headers)
                
                if user_info_response.status_code == 200:
                    st.session_state.user_info = user_info_response.json()
                    st.session_state.authenticated = True
                    st.query_params.clear() # Clear the URL so refreshing doesn't break it
                    st.rerun()
                else:
                    st.error("⚠️ Failed to retrieve profile from LinkedIn.")
            else:
                st.error("⚠️ Authentication failed. Please check your Client ID and Secret in your .env file.")

    else:
        # 4. Display the "Sign in with LinkedIn" Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("LinkSavvy requires your professional LinkedIn context to generate accurate brand content.")
            
            # Construct the secure OAuth 2.0 URL
            oauth_params = {
                "response_type": "code",
                "client_id": LINKEDIN_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "scope": "openid profile email",
                "state": "linksavvy_secure_state"
            }
            auth_link = f"{AUTH_URL}?{urllib.parse.urlencode(oauth_params)}"
            
            # Render a custom link that looks like a LinkedIn button
            st.markdown(f"""
            <a href="{auth_link}" target="_self" style="text-decoration: none;">
                <button style="width: 100%; padding: 12px; background-color: #0a66c2; color: white; border: none; border-radius: 24px; font-weight: bold; cursor: pointer; font-size: 16px;">
                    Sign in with LinkedIn
                </button>
            </a>
            """, unsafe_allow_html=True)

# ==========================================
# PART 3: YOUR ACTUAL APP (Properly Indented)
# ==========================================
else:
    # --- 1.5 PREMIUM UI STYLING (LinkedIn x SaaS Aesthetic) ---
    st.markdown("""
    <style>
        /* Hide Streamlit default branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Global Typography & Background */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Primary Button Styling (LinkedIn Blue) */
        .stButton>button {
            background-color: transparent;
            color: #e8e8e8;
            border: 1px solid #38434f;
            border-radius: 24px; /* Pill-shaped like ChatGPT/LinkedIn UI */
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #0a66c2; /* LinkedIn Brand Blue */
            color: white;
            border-color: #0a66c2;
            box-shadow: 0 0 10px rgba(10, 102, 194, 0.4);
            transform: scale(1.02);
        }

        /* Sidebar Clean-up */
        [data-testid="stSidebar"] {
            background-color: #1b1f23;
            border-right: 1px solid #2d333b;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            border-bottom-color: #0a66c2 !important;
            color: #0a66c2 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. SYSTEM PROMPT (The LinkedIn Persona) ---
    linksavvy_system_prompt = """
    You are LinkSavvy, a highly advanced LinkedIn Growth Strategist and Career Advisor.
    Your goal is to help the user build their personal brand and write highly engaging content.

    STRICT GUIDELINES:
    1. DWELL TIME PROTOCOL: Prioritize "Pattern Interrupt" hooks (surprising 1st sentences). Use the "1-3-1" structure (1 sentence, 3 bullet points, 1 punchline). Keep paragraphs to 1-2 lines maximum.
    2. LEXICAL DIVERSITY: Do NOT use AI cliches ("In today's fast-paced world", "Unleash your potential", "Let's dive in", "Delve"). Write like a confident, human professional.
    3. PERSONALIZATION: Always ground your advice in the specific facts provided in the "Memory Context" (e.g., their background as a Business Analyst, MBA, or specific projects).
    4. MULTIMODAL VISION: If an image is provided, act as a Brand Consultant. Critique the visual hook, text readability, and overall professional alignment for LinkedIn.
    5. GAP ANALYSIS: If a job description is provided, output a Markdown table comparing "Required Skill", "My Status", and "Action Item" using emojis.
    6. CONTENT PLANNING: If asked to plan content based on a document, extract 3 "Content Pillars" and format a calendar in a clean table.
    7. THE DATA MOAT: If the Memory Context includes a "[HIGH PERFORMING POST]", you MUST deeply analyze its formatting, hook style, and tone. Treat it as your primary template. Mimic its exact structure for the new draft, as it is statistically proven to work for this user's audience.
    """

    # --- 3. SESSION STATE INITIALIZATION ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_file_bytes" not in st.session_state:
        st.session_state.current_file_bytes = None
    if "current_file_name" not in st.session_state:
        st.session_state.current_file_name = None
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = [] # Stores our Kanban cards    

    # --- 4. UI SIDEBAR (Tabbed Organization) ---
    with st.sidebar:
        # Dynamically greet the LinkedIn user
        if st.session_state.user_info:
            first_name = st.session_state.user_info.get("given_name", "Creator")
            st.title(f"👋 Welcome, {first_name}")
        else:
            st.title("🔗 LinkSavvy")
            
        st.caption("Your Personal Brand Architect")
        
        # Create the tab navigation
        tab_tools, tab_data, tab_settings = st.tabs(["🛠️ Tools", "🗄️ Database", "⚙️ Settings"])
        
        with tab_tools:
            st.subheader("📄 Active Context")
            uploaded_file = st.file_uploader("Upload PDF, TXT, or Image", type=["pdf", "txt", "png", "jpg", "jpeg"], label_visibility="collapsed")
            audio_file = st.audio_input("Record a voice note")
            
            if uploaded_file:
                st.session_state.current_file_name = uploaded_file.name
                st.session_state.current_file_bytes = uploaded_file.getvalue()
            elif audio_file:
                st.session_state.current_file_name = "voice_note.wav"
                st.session_state.current_file_bytes = audio_file.getvalue()
            else:
                st.session_state.current_file_name = None
                st.session_state.current_file_bytes = None

            st.markdown("---")
            st.subheader("⚡ Core Actions")
            btn_ghostwrite = st.button("✍️ Ghostwrite Draft")
            btn_braindump = st.button("🎙️ Draft from Voice")
            btn_carousel = st.button("📄 Export PDF Carousel")
            btn_score_draft = st.button("📈 Score My Draft")
            
            # Tuck the rest of our powerful tools into an expander to keep the UI clean!
            with st.expander("🛠️ Advanced Strategy Tools"):
                btn_polish = st.button("✨ Polish Last Message")
                btn_draft_file = st.button("📝 Draft Post from File")
                btn_content_plan = st.button("📅 Generate Content Plan")
                btn_gap_analysis = st.button("📊 Career Gap Analysis")
                btn_hooks = st.button("🎣 Brainstorm 3 Hooks")
                btn_comment = st.button("💬 Comment Strategy")
                btn_matrix = st.button("🕸️ Competitor Matrix")
                btn_news = st.button("📰 News Hot Take")

            st.markdown("---")
            st.subheader("🎯 Hook Tracker")
            winning_hook = st.text_area("Log a winning hook:", height=80, label_visibility="collapsed", placeholder="Paste a hook that worked well...")
            if st.button("🏆 Save Hook"):
                if winning_hook.strip():
                    save_to_memory(f"[USER PREFERENCE - SUCCESSFUL HOOK STYLE]: {winning_hook}", source="Hook_Tracker", category="LinkedIn Brand")
                    st.success("✅ Hook logged!")
        with tab_data:
            st.subheader("💾 Save Current Context")
            
            # --- THE INVISIBLE TAGGING ENGINE ---
            if st.button("Save File to DB"):
                if st.session_state.get("current_file_bytes") is not None:
                    fname = st.session_state.current_file_name
                    fbytes = st.session_state.current_file_bytes
                    
                    with st.spinner(f"Categorizing and saving {fname}..."):
                        # 1. Extract the text
                        if fname.endswith(".pdf"): text_to_save = extract_text_from_pdf(fbytes)
                        elif fname.lower().endswith((".png", ".jpg", ".jpeg")): text_to_save = "Image uploaded (cannot parse text directly to DB)."
                        else: text_to_save = fbytes.decode("utf-8")
                        
                        if text_to_save.strip() and not text_to_save.startswith("Image"):
                            # 2. Ask AI to categorize the text
                            try:
                                cat_prompt = f"""
                                Read the following text and assign it EXACTLY ONE of these categories:
                                [Bzyday Project, Python Learning, LinkedIn Brand, Career Background, Competitor Research].
                                Respond with ONLY the exact category name. No other text.
                                Text: {text_to_save[:1000]}
                                """
                                cat_response = client.models.generate_content(
                                    model="gemini-2.5-flash-lite", 
                                    contents=cat_prompt
                                )
                                auto_category = cat_response.text.strip().replace("[", "").replace("]", "")
                            except Exception:
                                auto_category = "General" 
                                
                            # 3. Save with the new metadata
                            save_to_memory(text_to_save, source=fname, category=auto_category)
                            st.success(f"✅ Saved to DB! (Auto-Tagged as: {auto_category})")
                        else: 
                            st.error("⚠️ No readable text to save.")
                else: 
                    st.warning("⚠️ Upload a file first in the 'Tools' tab.")

            st.markdown("---")
            st.subheader("📊 Post Performance Tracker")
            st.caption("Feed your data moat. Log your successful posts here.")
            
            with st.form("performance_logger"):
                log_url = st.text_input("LinkedIn Post URL (Optional)")
                log_content = st.text_area("Paste the Post Content")
                
                col1, col2, col3 = st.columns(3)
                with col1: views = st.number_input("Views", min_value=0, step=100)
                with col2: likes = st.number_input("Likes", min_value=0, step=1)
                with col3: comments = st.number_input("Comments", min_value=0, step=1)
                
                if st.form_submit_button("💾 Save to Data Moat"):
                    if log_content.strip() and (views > 0 or likes > 0 or comments > 0):
                        # Calculate a crude "Engagement Score"
                        engagement_score = likes + (comments * 2) 
                        
                        memory_text = f"[HIGH PERFORMING POST] Views: {views} | Likes: {likes} | Comments: {comments} | Score: {engagement_score}\n\nContent: {log_content}"
                        
                        # Save to our vector DB with a specific category
                        save_to_memory(memory_text, source=log_url or "Manual_Entry", category="Proven_Content")
                        st.success(f"✅ Logged! LinkSavvy will study this for future drafts.")
                    else:
                        st.error("Please add content and at least some metric (views, likes, or comments).")        

            st.markdown("---")
            st.subheader("📈 Memory Analytics")
            stats = get_memory_analytics()
            if stats:
                col1, col2 = st.columns(2)
                col1.metric("Facts", stats["total_memories"])
                col2.metric("Chars", stats["total_characters"])
                st.bar_chart(stats["source_counts"])
            
            st.markdown("---")
            st.subheader("🗄️ Manage Entries")
            details = get_memory_details()
            if details["ids"]:
                with st.container(height=250):
                    for i in range(len(details["ids"])):
                        doc_id, doc_text, source = details["ids"][i], details["documents"][i], details["metadatas"][i].get("source", "Unknown")
                        col_text, col_btn = st.columns([5, 1])
                        with col_text: st.caption(f"**[{source}]** {doc_text[:30]}...")
                        with col_btn:
                            if st.button("❌", key=f"del_{doc_id}"): 
                                delete_memory(doc_id)
                                st.rerun()
                if st.button("🚨 Wipe All Memory"):
                    wipe_memory()
                    st.rerun()

        with tab_settings:
            st.subheader("AI Engine")
            selected_model = st.selectbox("Select Model:", ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.0-flash-lite"], label_visibility="collapsed")
            
            st.markdown("---")
            if st.button("🧹 Clear Current Chat"):
                st.session_state.messages = []
                st.rerun() 
            
            # NEW: Logout Button
            st.markdown("---")
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.rerun()

    # --- 5. MAIN UI TABS ---
    st.title("🔗 LinkSavvy: LinkedIn Assistant")
    
    # Split the main view into Chat and Kanban
    main_tab_chat, main_tab_pipeline = st.tabs(["💬 Assistant & Inbox", "📋 Content Pipeline"])
    
    with main_tab_chat:
        # --- 4.5 AGENT INBOX ---
        if os.path.exists("agent_drafts.json"):
            with open("agent_drafts.json", "r", encoding="utf-8") as f:
                try:
                    agent_drafts = json.load(f)
                except:
                    agent_drafts = []
                    
            pending_drafts = [d for d in agent_drafts if d.get("status") == "PENDING_REVIEW"]
            
            if pending_drafts:
                st.subheader("📬 Agent Inbox")
                st.info(f"✨ LinkSavvy drafted **{len(pending_drafts)}** post(s) in the background!")
                
                for i, draft in enumerate(pending_drafts):
                    with st.expander(f"📰 Breaking: {draft['source_title']}", expanded=True):
                        st.caption(f"Source: [Read Article]({draft['source_link']})")
                        edited_draft = st.text_area("Review Draft:", value=draft['draft_content'], height=200, key=f"draft_{i}")
                        
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if st.button("➡️ Send to Pipeline", key=f"approve_{i}"):
                                # Move from inbox to Kanban board!
                                new_card = {"id": len(st.session_state.pipeline) + 1, "content": edited_draft, "status": "Drafts"}
                                st.session_state.pipeline.append(new_card)
                                
                                # Mark as reviewed in JSON (Basic implementation)
                                agent_drafts[i]["status"] = "REVIEWED"
                                with open("agent_drafts.json", "w", encoding="utf-8") as file:
                                    json.dump(agent_drafts, file, indent=4)
                                st.success("Moved to Kanban Drafts!")
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Dismiss", key=f"dismiss_{i}"):
                                st.warning("Draft dismissed.")
                st.markdown("---")

        # --- 5.1 MAIN CHAT INTERFACE ---
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with main_tab_pipeline:
        # --- 5.2 THE KANBAN BOARD ---
        st.subheader("Content Pipeline")
        
        # Add a manual drafting button directly on the board
        new_idea = st.text_input("Quick Add New Draft:")
        if st.button("➕ Add to Board"):
            if new_idea:
                st.session_state.pipeline.append({"id": len(st.session_state.pipeline) + 1, "content": new_idea, "status": "Drafts"})
                st.rerun()

        st.markdown("---")
        
        # Create the 3 Kanban Columns
        col_drafts, col_review, col_ready = st.columns(3)
        
        # Helper function to move cards without refreshing the whole script manually
        def move_card(card_id, new_status):
            for card in st.session_state.pipeline:
                if card["id"] == card_id:
                    card["status"] = new_status

        # COLUMN 1: DRAFTS
        with col_drafts:
            st.markdown("<h4 style='text-align: center; color: #888;'>📝 Drafts</h4>", unsafe_allow_html=True)
            for card in st.session_state.pipeline:
                if card["status"] == "Drafts":
                    with st.container(border=True):
                        st.caption(f"Card #{card['id']}")
                        st.write(card["content"][:80] + "..." if len(card["content"]) > 80 else card["content"])
                        if st.button("Move to Review ➡️", key=f"d2r_{card['id']}"):
                            move_card(card["id"], "Review")
                            st.rerun()

        # COLUMN 2: REVIEW
        with col_review:
            st.markdown("<h4 style='text-align: center; color: #d97706;'>🧐 Review</h4>", unsafe_allow_html=True)
            for card in st.session_state.pipeline:
                if card["status"] == "Review":
                    with st.container(border=True):
                        st.caption(f"Card #{card['id']}")
                        st.write(card["content"][:80] + "..." if len(card["content"]) > 80 else card["content"])
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("⬅️ Back", key=f"r2d_{card['id']}"):
                                move_card(card["id"], "Drafts")
                                st.rerun()
                        with c2:
                            if st.button("Ready ➡️", key=f"r2ready_{card['id']}"):
                                move_card(card["id"], "Ready")
                                st.rerun()

        # COLUMN 3: READY
        with col_ready:
            st.markdown("<h4 style='text-align: center; color: #10b981;'>✅ Ready</h4>", unsafe_allow_html=True)
            for card in st.session_state.pipeline:
                if card["status"] == "Ready":
                    with st.container(border=True):
                        st.caption(f"Card #{card['id']}")
                        st.write(card["content"][:80] + "..." if len(card["content"]) > 80 else card["content"])
                        if st.button("⬅️ Review", key=f"ready2r_{card['id']}"):
                            move_card(card["id"], "Review")
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"del_{card['id']}"):
                            st.session_state.pipeline = [c for c in st.session_state.pipeline if c["id"] != card["id"]]
                            st.rerun()

    # --- 6. INPUT ROUTING ---
    user_input = st.chat_input("Ask LinkSavvy a question or paste a URL...")

    # Intercept Quick Action Buttons
    if btn_polish: user_input = "Please rewrite the last generated message. Make it more punchy, professional, and perfectly formatted for a LinkedIn audience."
    # NEW: Updated to trigger the Data Moat
    if btn_draft_file: user_input = "Draft a highly engaging LinkedIn post based purely on the currently uploaded file. Search your memory for my '[HIGH PERFORMING POST]' entries and use their exact formatting as your template."
    if btn_content_plan: user_input = "Analyze the uploaded document and my professional background. Extract 3 core 'Content Pillars' and create a 5-day LinkedIn content calendar formatted as a clean table."
    if btn_gap_analysis: user_input = "Analyze the provided Job Description URL or context against my background. Produce a structured 'Gap Analysis' table highlighting what I need to improve."
    # NEW: Updated to trigger the Data Moat
    if btn_ghostwrite: user_input = "Write a LinkedIn post about a recent professional insight. Search your memory for any '[HIGH PERFORMING POST]' entries and mimic their exact tone and structure."
    if btn_hooks: user_input = "Analyze the provided context and brainstorm 3 distinct, high-impact LinkedIn hooks for a post. Provide a brief 1-sentence explanation of why each hook works."
    if btn_braindump: user_input = "Listen to the attached voice note. Extract the core insights and transform my messy thoughts into a highly engaging, 360Brew-compliant LinkedIn post using the 1-3-1 structure."
    if btn_carousel: user_input = """
        Based on my memory context or the attached file, draft a 5-slide LinkedIn Carousel.
        CRITICAL INSTRUCTION: You MUST start every single slide with the exact text '[SLIDE]'. 
        Keep the text on each slide extremely short (max 3 sentences). 
        Make Slide 1 a strong hook. Make Slide 5 a Call to Action.
        """
    if btn_comment: user_input = """
        Analyze the provided LinkedIn post (either from the pasted text or URL). 
        Cross-reference this post with my professional background in your memory.
        Generate 3 distinct, highly engaging comments I can leave on this post:
        
        1. 'The Value Add': Add a new, specific insight based on my background.
        2. 'The Respectful Contrarian': Politely offer a different perspective or edge case.
        3. 'The Story Relater': Share a brief, relevant 1-sentence personal experience.
        
        CRITICAL: Keep each comment under 3 sentences. Do NOT use generic praise like "Great post!" or "Thanks for sharing." Start directly with the hook.
        """ 
    if btn_score_draft: user_input = """
        Analyze the provided draft LinkedIn post against the 2026 '360Brew' algorithm protocols.
        Provide a strict grading scorecard formatted EXACTLY like this:
        
        ## 📈 Algorithm Prediction Score
        * **Hook Strength:** [Score / 20] 
        * **Lexical Diversity (No AI cliches):** [Score / 20]
        * **Dwell Time Formatting (White space, 1-3-1):** [Score / 20]
        * **Authority/Authenticity:** [Score / 20]
        * **Call to Action/Engagement Loop:** [Score / 20]
        
        ### 🏆 TOTAL SCORE: [Total / 100]
        
        **Verdict:** [Pass (Ready to Post) / Fail (Needs Revision)]
        
        **Top 2 Critical Fixes:**
        1. [Fix 1]
        2. [Fix 2]
        
        Be brutally honest. If it sounds like generic AI, fail it.
        """    
    if btn_matrix: user_input = """
        Analyze the provided competitor URLs or Job Descriptions. 
        1. Extract the top 10 most frequently mentioned hard skills or keywords.
        2. Cross-reference them against my professional memory context.
        3. Output a detailed Markdown table with columns: 'Skill', 'Competency Mentioned', and 'My Experience Level'.
        4. Provide a 2-sentence analytical summary on how to close the biggest skill gap.
        """   
    if btn_news:
        user_input = """
        Analyze the provided news article URL(s).
        1. Summarize the core business event or tech trend in exactly 1 sentence.
        2. Cross-reference this trend with my professional background in your memory.
        3. Write a "Hot Take" LinkedIn post connecting the news to my industry perspective.
        4. Provide 2 variations: One 'Optimistic' and one 'Contrarian/Warning'.
        5. Use the 360Brew protocol: 1-3-1 formatting, no AI cliches, punchy hooks.
        """        
    # --- 7. ORCHESTRATION & API CALL ---
    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Gather Extra Context
        extracted_context = ""
        
        # NEW: Use Regex to find ALL URLs in the user's message
        urls = re.findall(r'(https?://[^\s]+)', user_input)
        
        if urls:
            with st.chat_message("assistant"):
                with st.spinner(f"Scraping {len(urls)} link(s)..."):
                    for url in urls:
                        scraped_text = scrape_linkedin_url(url)
                        extracted_context += f"\n--- Data from {url} ---\n{scraped_text}\n"
                    st.success(f"✅ Successfully extracted data from {len(urls)} source(s).")
        
        memory_context = recall_from_memory(user_input)
            
        # Initialize Multimodal Parts List
        user_content_parts = [types.Part.from_text(text=user_input)]
        
        if extracted_context:
            user_content_parts.append(types.Part.from_text(text=f"\nhttps://www.merriam-webster.com/dictionary/context: {extracted_context}"))
        if memory_context:
            user_content_parts.append(types.Part.from_text(text=f"\n[Memory Context]: {memory_context}"))
            
        # Inject File / Image Context
        if st.session_state.get("current_file_bytes") is not None:
            fname = st.session_state.current_file_name
            fbytes = st.session_state.current_file_bytes
            
            with st.chat_message("assistant"):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.image(fbytes, caption=f"Analyzing {fname}", width=250)
                    # Correctly assign the MIME type based on file extension
                    mime = "image/png" if fname.lower().endswith(".png") else "image/jpeg"
                    user_content_parts.append(types.Part.from_bytes(data=fbytes, mime_type=mime))
                    user_content_parts.append(types.Part.from_text(text="[SYSTEM OVERRIDE: Analyze the attached image as requested.]"))
                
                # NEW: Audio Logic
                elif fname.lower().endswith(".wav"):
                    st.audio(fbytes, format="audio/wav")
                    user_content_parts.append(types.Part.from_bytes(data=fbytes, mime_type="audio/wav"))
                    user_content_parts.append(types.Part.from_text(text="[SYSTEM OVERRIDE: Transcribe and analyze the attached audio file.]"))

                else:
                    with st.spinner(f"📄 Reading {fname}..."):
                        if fname.endswith(".pdf"): text_content = extract_text_from_pdf(fbytes)
                        else: text_content = fbytes.decode("utf-8")
                        
                        if text_content.strip():
                            user_content_parts.append(types.Part.from_text(text=f"\n[File Context ({fname})]:\n{text_content}"))
                            user_content_parts.append(types.Part.from_text(text="[SYSTEM OVERRIDE: Prioritize the File Context above when answering.]"))

        # Execute Gemini API Call safely
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data & generating response..."):
                try:
                    # Build conversation history in correct Part format
                    formatted_history = []
                    for msg in st.session_state.messages[:-1]:
                        role = "user" if msg["role"] == "user" else "model"
                        formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
                    
                    # Append the newly built current message
                    formatted_history.append(types.Content(role="user", parts=user_content_parts))

                    response = client.models.generate_content(
                        model=selected_model,
                        contents=formatted_history,
                        config=types.GenerateContentConfig(
                            system_instruction=linksavvy_system_prompt,
                            temperature=0.7 
                        )
                    )
                    
                    assistant_reply = response.text
                    st.markdown(assistant_reply)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                    # --- NEW: One-Click Markdown Export ---
                    st.download_button(
                        label="⬇️ Download as .md",
                        data=assistant_reply,
                        file_name="LinkSavvy_Draft.md",
                        mime="text/markdown",
                        key=f"export_{len(st.session_state.messages)}"
                    )

                    # NEW: Check if this was a carousel draft and offer PDF download
                    if "[SLIDE]" in assistant_reply:
                        st.success("✅ Carousel formatting detected!")
                        pdf_bytes = create_pdf_carousel(assistant_reply)
                        st.download_button(
                            label="📥 Download PDF Carousel for LinkedIn",
                            data=pdf_bytes,
                            file_name="LinkSavvy_Carousel.pdf",
                            mime="application/pdf"
                        )
                    
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        st.error("🚨 Quota Exceeded! The free tier limit was reached. Wait 60 seconds, or select 'gemini-1.5-flash-8b' from the sidebar and try again.")
                    else:
                        st.error(f"API Error: {e}")