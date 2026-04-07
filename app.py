import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import re
from tools import scrape_linkedin_url # Importing our custom tool

# Load environment variables
load_dotenv()

# Initialize API Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("🚨 API Key not found! Please check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

# Page Configuration
st.set_page_config(page_title="LinkSavvy", page_icon="🔗", layout="centered")

# --- LinkSavvy Persona ---
linksavvy_system_prompt = """You are LinkSavvy, an elite LinkedIn growth strategist, technical copywriter, and professional branding assistant.
Your sole purpose is to help the user craft high-impact LinkedIn content, optimize their professional profile, and strategize networking.

Guidelines you must strictly follow:
1. Tone: Professional, insightful, engaging, and free of typical "AI fluff" (avoid words like "delve", "testament", or "tapestry").
2. Formatting: Always format LinkedIn posts with short, punchy sentences, clear line breaks, and 3-5 highly relevant hashtags.
3. Domain Expertise: You have deep expertise in business analytics, marketing strategies, and the lifecycle of enterprise software development (such as CRM and ERP platforms). When the user asks for post ideas or profile summaries, lean into these analytical and strategic themes unless instructed otherwise.
4. If the user asks a question entirely unrelated to professional growth, career, or LinkedIn, gently guide them back to your primary purpose."""

# --- UI Sidebar ---
with st.sidebar:
    st.title("⚙️ LinkSavvy Settings")
    st.markdown("Select your AI Engine:")
    
    # Dropdown for the free-tier models
    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"],
        index=0
    )
    st.caption("All models above are operating on the free tier.")

# --- Main UI ---
st.title("🔗 LinkSavvy: LinkedIn Assistant")
st.write("Welcome to your dedicated AI companion for LinkedIn growth.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Logic
if prompt := st.chat_input("Ask LinkSavvy a question..."):
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- ORCHESTRATION LAYER: Check for URLs ---
    url_match = re.search(r'(https?://[^\s]+)', prompt)
    extracted_context = ""
    
    if url_match:
        target_url = url_match.group(0)
        with st.chat_message("assistant"):
            with st.spinner(f"🔗 Extracting data from URL..."):
                scraped_text = scrape_linkedin_url(target_url)
                # We package this so the AI knows what it's looking at
                extracted_context = f"\n\n--- EXTRACTED WEBSITE CONTEXT ---\n{scraped_text}\n---------------------------------\n"
                st.success("Successfully read the link context!")

    # --- LLM CALL ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # 1. Build the conversation history
                formatted_history = []
                for msg in st.session_state.messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    formatted_history.append(
                        types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                    )
                
                # 2. Combine the prompt with any extracted context
                final_prompt = prompt
                if extracted_context:
                    final_prompt = prompt + extracted_context

                # 3. Add the final combined prompt
                formatted_history.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=final_prompt)])
                )

                # 4. Send to Gemini
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
                # Append assistant message (we only save the clean reply to history)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                st.error(f"An error occurred: {e}")