import os
import streamlit as st
from google import genai
from google.genai import types  # NEW: Required for model configuration
from supabase import create_client, Client
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_email():
    """Helper to securely get the current logged-in user's email."""
    if 'user_info' in st.session_state and st.session_state.user_info:
        return st.session_state.user_info.get("email", "unknown@user.com")
    return "unknown@user.com"

def get_embedding(text):
    """Generates a 768-dimensional vector embedding using the new Gemini model."""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        # We MUST force 768 dimensions so it matches our Postgres schema!
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return response.embeddings[0].values

def save_to_memory(text, source="user", category="general"):
    """Embeds text and saves it securely to the user's Supabase cloud table."""
    email = get_user_email()
    embedding = get_embedding(text) # Translate text to math
    
    data = {
        "user_email": email,
        "content": text,
        "source": source,
        "category": category,
        "embedding": embedding
    }
    supabase.table("ai_memory").insert(data).execute()

def recall_from_memory(query, threshold=0.4, match_count=5):
    """Searches Postgres for mathematically similar memories."""
    email = get_user_email()
    query_embedding = get_embedding(query)
    
    # Call the powerful Postgres Similarity Search function we just built!
    response = supabase.rpc("match_memories", {
        "query_embedding": query_embedding,
        "match_email": email,
        "match_threshold": threshold,
        "match_count": match_count
    }).execute()
    
    matches = response.data
    
    if not matches:
        return ""
        
    context = ""
    for match in matches:
        context += f"\n- [{match['category']} | Source: {match['source']}]: {match['content']}"
        
    return context

def get_memory_analytics():
    """Fetches stats directly from the cloud for the UI dashboard."""
    email = get_user_email()
    response = supabase.table("ai_memory").select("content, source").eq("user_email", email).execute()
    data = response.data
    
    if not data:
        return None
        
    total_memories = len(data)
    total_chars = sum(len(row["content"]) for row in data)
    
    source_counts = {}
    for row in data:
        src = row.get("source", "Unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
        
    return {
        "total_memories": total_memories,
        "total_characters": total_chars,
        "source_counts": source_counts
    }

def get_memory_details():
    """Formats the cloud data to perfectly match what app.py expects."""
    email = get_user_email()
    response = supabase.table("ai_memory").select("id, content, source, category").eq("user_email", email).execute()
    data = response.data
    
    ids = [row["id"] for row in data]
    documents = [row["content"] for row in data]
    metadatas = [{"source": row["source"], "category": row["category"]} for row in data]
    
    return {"ids": ids, "documents": documents, "metadatas": metadatas}

def delete_memory(doc_id):
    """Deletes a specific memory from the cloud."""
    email = get_user_email()
    supabase.table("ai_memory").delete().eq("id", doc_id).eq("user_email", email).execute()

def wipe_memory():
    """Wipes all memories from the cloud for the current user."""
    email = get_user_email()
    supabase.table("ai_memory").delete().eq("user_email", email).execute()
    
def get_all_memories():
    """Fallback function for backward compatibility."""
    return get_memory_details()