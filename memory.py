import chromadb

# Initialize the local ChromaDB client (saves to a folder named 'chroma_data')
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Create or get the collection (our specific database table)
collection = chroma_client.get_or_create_collection(name="linksavvy_memory")

def save_to_memory(text, source="user_input"):
    """Saves a piece of text to the local vector database."""
    import uuid
    doc_id = str(uuid.uuid4())
    
    collection.add(
        documents=[text],
        metadatas=[{"source": source}],
        ids=[doc_id]
    )
    return True

def recall_from_memory(query, n_results=2):
    """Searches the database for information relevant to the user's query."""
    if collection.count() == 0:
        return ""
        
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )
    
    if results['documents'] and results['documents'][0]:
        # Combine the found memories into a single string
        return "\n".join(results['documents'][0])
    return ""

def get_all_memories():
    """Retrieves all documents currently stored in the database."""
    if collection.count() == 0:
        return []
    results = collection.get() 
    return results['documents']

def wipe_memory():
    """Deletes all items in the current collection."""
    if collection.count() > 0:
        results = collection.get()
        collection.delete(ids=results['ids'])
    return True

def get_memory_analytics():
    """Extracts structured data from ChromaDB for analytics visualization."""
    if collection.count() == 0:
        return None
        
    results = collection.get()
    
    # Python dictionary to count how many facts came from each source
    source_counts = {}
    for meta in results['metadatas']:
        # Fallback to 'Unknown' if the source isn't labeled
        src = meta.get('source', 'Unknown') 
        source_counts[src] = source_counts.get(src, 0) + 1
        
    # Calculate the total volume of text stored
    total_chars = sum(len(doc) for doc in results['documents'])
    
    return {
        "total_memories": collection.count(),
        "total_characters": total_chars,
        "source_counts": source_counts
    }