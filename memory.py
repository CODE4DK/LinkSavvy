# memory.py
import chromadb
import uuid
import os

# 1. Initialize a persistent local database directory
# This will create a folder called 'chroma_data' in your project
db_path = os.path.join(os.getcwd(), "chroma_data")
chroma_client = chromadb.PersistentClient(path=db_path)

# 2. Create or connect to a 'collection' (similar to a table in SQL)
collection = chroma_client.get_or_create_collection(name="linksavvy_knowledge")

def save_to_memory(text_content, source="user_input"):
    """Saves a piece of text into the long-term vector database."""
    doc_id = str(uuid.uuid4()) # Generate a unique ID for this memory
    
    collection.add(
        documents=[text_content],
        metadatas=[{"source": source}],
        ids=[doc_id]
    )
    return True

def recall_from_memory(query, n_results=2):
    """Searches the database for content mathematically related to the query."""
    # If the database is empty, return early
    if collection.count() == 0:
        return []
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Extract and return the matched text documents
    if results['documents'] and results['documents'][0]:
        return results['documents'][0]
    return []

def get_all_memories():
    """Retrieves all documents currently stored in the database."""
    if collection.count() == 0:
        return []
    
    # .get() without parameters returns everything in the collection
    results = collection.get() 
    return results['documents']

def wipe_memory():
    """Deletes all items in the current collection."""
    if collection.count() > 0:
        # Get all IDs and delete them
        results = collection.get()
        collection.delete(ids=results['ids'])
    return True

# --- Local Testing Block ---
if __name__ == "__main__":
    print("🧠 Initializing LinkSavvy's Brain...")
    
    # 1. Store some test facts
    print("Saving memories...")
    save_to_memory("I am a Business Analyst currently working on developing a CRM and ERP platform called Bzyday.")
    save_to_memory("My target LinkedIn audience is project managers and software developers.")
    save_to_memory("I prefer my posts to have a hook, 3 bullet points, and a strong call to action.")
    
    # 2. Test semantic retrieval
    print("\n🔍 Testing Recall:")
    test_query = "What product am I building?"
    print(f"Asking: '{test_query}'")
    
    recalled_info = recall_from_memory(test_query)
    
    print("\n--- Retrieved Memories ---")
    for info in recalled_info:
        print(f"- {info}")
    print("--------------------------")