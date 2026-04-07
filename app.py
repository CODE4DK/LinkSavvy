import streamlit as st
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tools import scrape_linkedin_url, extract_text_from_pdf, chunk_text
from memory import save_to_memory, recall_from_memory, get_all_memories, wipe_memory

# --- 1. SETUP & CONFIG ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="LinkSavvy: LinkedIn Assistant", layout="wide")

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
"""

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_file_bytes" not in st.session_state:
    st.session_state.current_file_bytes = None
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None

# --- 4. UI SIDEBAR ---
with st.sidebar:
    st.title("⚙️ LinkSavvy Settings")
    # Using only the highest-limit free models to minimize quota errors
    selected_model = st.selectbox("Select AI Engine:", [
        "gemini-2.5-flash-lite", # The fastest, most forgiving free model
        "gemini-3.1-flash-lite",   # Extremely lightweight fallback
        "gemini-2.0-flash-lite"       # The smartest, but strictest quota
    ])
    
    st.markdown("---")
    st.subheader("📄 Upload Context")
    st.write("Upload PDF, TXT, or Image (PNG/JPG)")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        st.success(f"Attached: {uploaded_file.name}")
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.current_file_bytes = uploaded_file.getvalue()
    else:
        st.session_state.current_file_name = None
        st.session_state.current_file_bytes = None

    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    btn_polish = st.button("✨ Polish Last Message")
    btn_draft_file = st.button("📝 Draft Post from File")
    btn_content_plan = st.button("📅 Generate Content Plan")
    btn_gap_analysis = st.button("📊 Career Gap Analysis")
    btn_ghostwrite = st.button("✍️ Ghostwrite My Voice")
    btn_hooks = st.button("🎣 Brainstorm 3 Hooks")
    btn_save_file = st.button("💾 Save File to Database")
    btn_clear_chat = st.button("🧹 Clear Chat History")

    # Clear Chat Logic
    if btn_clear_chat:
        st.session_state.messages = []
        st.rerun()

    # Save to Database Logic
    if btn_save_file:
        if st.session_state.get("current_file_bytes") is not None:
            fname = st.session_state.current_file_name
            fbytes = st.session_state.current_file_bytes
            with st.spinner(f"Saving {fname} to memory..."):
                if fname.endswith(".pdf"): text_to_save = extract_text_from_pdf(fbytes)
                elif fname.lower().endswith((".png", ".jpg", ".jpeg")): text_to_save = "Image uploaded (cannot parse text directly to DB yet)."
                else: text_to_save = fbytes.decode("utf-8")
                
                if text_to_save.strip():
                    save_to_memory(text_to_save, source=fname)
                    st.success(f"✅ Saved {fname} to ChromaDB!")
                else: st.error("⚠️ No readable text to save.")
        else: st.warning("⚠️ Upload a file first.")

    st.markdown("---")
    with st.expander("🗄️ Database Dashboard"):
        st.write("View or clear long-term memory.")
        all_memories = get_all_memories()
        if not all_memories: st.info("Database is empty.")
        else:
            st.success(f"Total facts: {len(all_memories)}")
            for i, mem in enumerate(all_memories): st.caption(f"{i+1}. {mem[:80]}...") 
        if st.button("🚨 Wipe All Memory"):
            wipe_memory()
            st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
st.title("🔗 LinkSavvy: LinkedIn Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. INPUT ROUTING ---
user_input = st.chat_input("Ask LinkSavvy a question or paste a URL...")

# Intercept Quick Action Buttons
if btn_polish: user_input = "Please rewrite the last generated message. Make it more punchy, professional, and perfectly formatted for a LinkedIn audience."
if btn_draft_file: user_input = "Draft a highly engaging LinkedIn post based purely on the currently uploaded file. Ensure it has a strong hook, 3 short bullet points, and a clear call to action."
if btn_content_plan: user_input = "Analyze the uploaded document and my professional background. Extract 3 core 'Content Pillars' and create a 5-day LinkedIn content calendar formatted as a clean table."
if btn_gap_analysis: user_input = "Analyze the provided Job Description URL or context against my background. Produce a structured 'Gap Analysis' table highlighting what I need to improve."
if btn_ghostwrite: user_input = "Write a LinkedIn post about a recent professional insight. Use the '1-3-1' structure for maximum dwell time. Ensure the tone is 'Confident but Human'."
if btn_hooks: user_input = "Analyze the provided context and brainstorm 3 distinct, high-impact LinkedIn hooks for a post. Provide a brief 1-sentence explanation of why each hook works."

# --- 7. ORCHESTRATION & API CALL ---
if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Gather Extra Context
    extracted_context = ""
    if "linkedin.com" in user_input or "http" in user_input:
        extracted_context = scrape_linkedin_url(user_input)
    
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
                
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error("🚨 Quota Exceeded! The free tier limit was reached. Wait 60 seconds, or select 'gemini-1.5-flash-8b' from the sidebar and try again.")
                else:
                    st.error(f"API Error: {e}")