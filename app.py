import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import re
from tools import scrape_linkedin_url, extract_text_from_pdf
from memory import save_to_memory, recall_from_memory, get_all_memories, wipe_memory

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
    
    st.markdown("---")
    st.subheader("📄 Upload Document")
    st.write("Upload a PDF or TXT for temporary session context.")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt"])

    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    st.write("One-click prompts for faster workflows.")

    st.markdown("---")
    # --- Memory Dashboard ---
    with st.expander("🗄️ Database Dashboard"):
        st.write("View or clear LinkSavvy's long-term memory.")
        
        # 1. Fetch and display memories
        all_memories = get_all_memories()
        
        if not all_memories:
            st.info("Database is currently empty.")
        else:
            st.success(f"Total saved facts: {len(all_memories)}")
            # Loop through and display a preview of each memory
            for i, mem in enumerate(all_memories):
                # Show only the first 100 characters to keep the UI clean
                st.caption(f"{i+1}. {mem[:100]}...") 
                
        # 2. Add the wipe button
        if st.button("🚨 Wipe All Database Memory"):
            wipe_memory()
            st.rerun() # Instantly refreshes the UI to show the empty state
    
    # Existing buttons
    btn_polish = st.button("✨ Polish Last Message")
    btn_draft_file = st.button("📝 Draft Post from File")
    btn_save_file = st.button("💾 Save File to Database") 

    btn_clear_chat = st.button("🧹 Clear Chat History")
    if btn_clear_chat:
        st.session_state.messages = [] # Empties the chat memory
        # Note: We do not clear the uploaded file here, so you can keep chatting about the same file!
        st.rerun() # Instantly refreshes the UI to show a clean slate

    # NEW: Hook Generator Button
    btn_generate_hooks = st.button("🎣 Brainstorm Hooks")    
    
    # NEW: Save the file to session state so it survives chat reruns
    if uploaded_file:
        st.success(f"Attached: {uploaded_file.name}")
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.current_file_bytes = uploaded_file.getvalue()
    else:
        # Clear it if the user clicks the 'X' to remove the file
        st.session_state.current_file_name = None
        st.session_state.current_file_bytes = None

    # Dropdown for the free-tier models
    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"],
        index=0
    )
    st.caption("All models above are operating on the free tier.")
    st.markdown("---")
    st.subheader("🧠 Teach LinkSavvy")
    st.write("Save facts about your career, audience, or style.")
    new_fact = st.text_area("Fact to remember:", height=100)
    if st.button("Save to Memory"):
        if new_fact:
            save_to_memory(new_fact)
            st.success("Saved to long-term memory!")
        else:
            st.warning("Please enter a fact first.")

# --- Logic for "Save File to Database" Button ---
if btn_save_file:
    if st.session_state.get("current_file_bytes") is not None:
        file_name = st.session_state.current_file_name
        file_bytes = st.session_state.current_file_bytes
        
        with st.spinner(f"Saving {file_name} to permanent memory..."):
            # Extract the text
            if file_name.endswith(".pdf"):
                text_to_save = extract_text_from_pdf(file_bytes)
            else:
                text_to_save = file_bytes.decode("utf-8")
                
            # Save to ChromaDB
            if text_to_save and text_to_save.strip():
                save_to_memory(text_to_save, source=file_name)
                st.success(f"✅ Successfully and permanently saved the contents of {file_name} to ChromaDB!")
            else:
                st.error("⚠️ Could not extract readable text to save.")
    else:
        st.warning("⚠️ Please upload a file in the sidebar first.")            

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

# --- Chat Input & Logic ---
# 1. Capture input from EITHER the chat box OR a Quick Action button
user_input = st.chat_input("Ask LinkSavvy a question...")

if btn_polish:
    user_input = "Please rewrite the last generated message. Make it more punchy, professional, and perfectly formatted for a LinkedIn audience."
if btn_draft_file:
    user_input = "Draft a highly engaging LinkedIn post based purely on the currently uploaded file. Ensure it has a strong hook, 3 short bullet points, and a clear call to action."
if btn_generate_hooks:
    user_input = "Analyze the provided context (either the uploaded file, database memory, or URL) and brainstorm 3 distinct, high-impact LinkedIn hooks for a post. Do NOT write the full post yet. Provide a brief 1-sentence explanation of the psychology behind why each hook works. Label them Hook 1, Hook 2, and Hook 3."

# 2. Trigger the orchestration if an input exists
if user_input:
    prompt = user_input
    
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- ORCHESTRATION LAYER: Data Gathering ---
    extracted_context = ""
    memory_context = ""
    
    # 1. Check for URLs
    url_match = re.search(r'(https?://[^\s]+)', prompt)
    if url_match:
        target_url = url_match.group(0)
        with st.chat_message("assistant"):
            with st.spinner(f"🔗 Extracting data from URL..."):
                scraped_text = scrape_linkedin_url(target_url)
                extracted_context = f"\n\n--- EXTRACTED WEBSITE CONTEXT ---\n{scraped_text}\n---------------------------------\n"
                st.success("Successfully read the link context!")

    # 2. Query Long-Term Memory
    # We search the database for anything mathematically related to the user's prompt
    relevant_memories = recall_from_memory(prompt)
    if relevant_memories:
        memory_context = "\n\n--- RELEVANT BACKGROUND KNOWLEDGE ---\n"
        for mem in relevant_memories:
            memory_context += f"- {mem}\n"
        memory_context += "-------------------------------------\n"

    # 3. Check for Uploaded File Context
    file_context = ""
    if st.session_state.get("current_file_bytes") is not None:
        file_name = st.session_state.current_file_name
        file_bytes = st.session_state.current_file_bytes
        
        with st.chat_message("assistant"):
            with st.spinner(f"📄 Reading {file_name}..."):
                if file_name.endswith(".pdf"):
                    extracted_doc_text = extract_text_from_pdf(file_bytes)
                else:
                    extracted_doc_text = file_bytes.decode("utf-8")
                
                if not extracted_doc_text or not extracted_doc_text.strip():
                    st.warning("⚠️ The file was attached, but I couldn't extract any readable text from it. (If it's a PDF, it might be an image/scan).")
                else:
                    st.success(f"✅ Successfully extracted {len(extracted_doc_text)} characters from the file!")
                    file_context = f"\n\n--- UPLOADED DOCUMENT CONTEXT ({file_name}) ---\n{extracted_doc_text}\n---------------------------------------\n"

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
                
                # 2. Combine all context safely
                final_prompt = prompt
                if extracted_context:
                    final_prompt += extracted_context
                if memory_context:
                    final_prompt += memory_context
                if file_context:
                    # We inject a strict system override so the AI doesn't get confused by its own limitations
                    final_prompt += f"\n\n[SYSTEM OVERRIDE: The user has provided file text below. DO NOT say you cannot read files. Analyze this text directly:] {file_context}"

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
                # Append assistant message
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                st.error(f"An error occurred: {e}")