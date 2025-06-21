"""
ChromaDB Tutorial - Complete Guide
This tutorial shows how to use ChromaDB for vector database operations
"""

import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer
import pandas as pd

def basic_chromadb_usage():
    """Basic ChromaDB operations"""
    print("🔵 Basic ChromaDB Usage")
    print("=" * 40)
    
    # 1. Create a client (in-memory database)
    client = chromadb.Client()
    
    # 2. Create a collection (like a table in SQL)
    collection = client.create_collection(name="my_collection")
    
    # 3. Add documents with embeddings
    documents = [
        "I love programming",
        "Python is great for data science",
        "Machine learning is fascinating",
        "I enjoy building applications"
    ]
    
    # Simple embeddings (in real use, you'd use a proper embedding model)
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.2, 0.3, 0.4, 0.5],
        [0.3, 0.4, 0.5, 0.6],
        [0.4, 0.5, 0.6, 0.7]
    ]
    
    # Add documents
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=["doc1", "doc2", "doc3", "doc4"]
    )
    
    # 4. Query the collection
    results = collection.query(
        query_embeddings=[[0.1, 0.2, 0.3, 0.4]],
        n_results=2
    )
    
    print("Query Results:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc}")
    
    print()

def persistent_chromadb():
    """Using ChromaDB with persistent storage"""
    print("🟢 Persistent ChromaDB")
    print("=" * 40)
    
    # Create persistent client
    client = chromadb.PersistentClient(
        path="./my_chromadb",  # Database will be saved here
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Get or create collection
    try:
        collection = client.get_collection(name="persistent_collection")
        print("✅ Loaded existing collection")
    except:
        collection = client.create_collection(
            name="persistent_collection",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        print("✅ Created new collection")
    
    # Check if collection has data
    count = collection.count()
    print(f"📊 Collection has {count} documents")
    
    if count == 0:
        # Add some data
        documents = [
            "ChromaDB is a vector database",
            "It supports similarity search",
            "You can store embeddings efficiently",
            "Perfect for RAG applications"
        ]
        
        # Generate embeddings using sentence transformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(documents)
        
        collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            ids=[f"persistent_doc_{i}" for i in range(len(documents))],
            metadatas=[{"topic": "chromadb", "index": i} for i in range(len(documents))]
        )
        print("✅ Added documents to collection")
    
    # Search in collection
    query = "What is a vector database?"
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query])
    
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=2,
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\nSearch results for: '{query}'")
    for i, doc in enumerate(results['documents'][0]):
        distance = results['distances'][0][i]
        similarity = 1 - distance
        print(f"  {i+1}. {doc} (similarity: {similarity:.3f})")
    
    print()

def advanced_chromadb_features():
    """Advanced ChromaDB features"""
    print("🟡 Advanced ChromaDB Features")
    print("=" * 40)
    
    client = chromadb.PersistentClient(path="./advanced_chromadb")
    
    # Create collection with custom distance function
    try:
        client.delete_collection(name="advanced_collection")
    except:
        pass
    
    collection = client.create_collection(
        name="advanced_collection",
        metadata={
            "hnsw:space": "cosine",  # cosine, l2, ip (inner product)
            "hnsw:construction_ef": 200,
            "hnsw:M": 16
        }
    )
    
    # Sample customer support data
    tickets = [
        {"id": "T001", "subject": "Login issue", "description": "Cannot login to my account", "priority": "high"},
        {"id": "T002", "subject": "Password reset", "description": "Forgot my password need help", "priority": "medium"},
        {"id": "T003", "subject": "Billing problem", "description": "Wrong charge on my credit card", "priority": "high"},
        {"id": "T004", "subject": "Feature request", "description": "Please add dark mode to app", "priority": "low"},
        {"id": "T005", "subject": "App crash", "description": "App keeps crashing on iPhone", "priority": "high"}
    ]
    
    # Generate embeddings for tickets
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    documents = []
    metadatas = []
    ids = []
    
    for ticket in tickets:
        # Combine subject and description for better embeddings
        text = f"{ticket['subject']} {ticket['description']}"
        documents.append(text)
        metadatas.append({
            "ticket_id": ticket["id"],
            "subject": ticket["subject"],
            "priority": ticket["priority"]
        })
        ids.append(ticket["id"])
    
    embeddings = model.encode(documents)
    
    # Add to collection
    collection.add(
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    # Advanced queries
    print("🔍 Advanced Query Examples:")
    
    # 1. Basic similarity search
    query = "I can't access my account"
    query_embedding = model.encode([query])
    
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=3,
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\n1. Similar tickets for: '{query}'")
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        metadata = results['metadatas'][0][i]
        similarity = 1 - results['distances'][0][i]
        print(f"   {metadata['ticket_id']}: {metadata['subject']} (similarity: {similarity:.3f})")
    
    # 2. Filtered search (only high priority)
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=5,
        where={"priority": "high"},  # Filter by metadata
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\n2. High priority tickets similar to: '{query}'")
    for i in range(len(results['documents'][0])):
        metadata = results['metadatas'][0][i]
        similarity = 1 - results['distances'][0][i]
        print(f"   {metadata['ticket_id']}: {metadata['subject']} (similarity: {similarity:.3f})")

def your_project_rag_usage():
    """How ChromaDB is used in your RAG service"""
    print("🚀 Your Project's RAG Implementation")
    print("=" * 40)
    
    print("📁 File: rag_service.py")
    print("""
Key Components:

1. **Initialization:**
   client = chromadb.PersistentClient(
       path="./chroma_db",
       settings=Settings(anonymized_telemetry=False, allow_reset=True)
   )

2. **Collection Creation:**
   collection = client.create_collection(
       name="customer_support_tickets",
       metadata={"hnsw:space": "cosine"}
   )

3. **Data Loading (29K+ tickets):**
   - Reads customer_support_tickets.csv
   - Combines: subject + description + type + product
   - Generates embeddings using 'all-MiniLM-L6-v2'
   - Stores in batches of 100 for memory efficiency

4. **Search Process:**
   - User query → embedding
   - ChromaDB cosine similarity search
   - Returns top N similar tickets with scores

5. **Metadata Storage:**
   - ticket_id, customer_name, subject, description
   - ticket_type, product, status, priority
   - resolution, satisfaction_rating
    """)
    
    print("\n📊 Your RAG Database Stats:")
    print("- Total tickets: 29,808")
    print("- Vector dimensions: 384")
    print("- Similarity metric: Cosine")
    print("- Storage: ~50MB")
    print("- Search speed: <1 second")

def chromadb_best_practices():
    """Best practices for ChromaDB"""
    print("💡 ChromaDB Best Practices")
    print("=" * 40)
    
    practices = [
        "1. **Choose Right Distance Metric:**",
        "   - Cosine: Good for text similarity (your choice ✅)",
        "   - L2: Good for spatial data",
        "   - Inner Product: Good for recommendation systems",
        "",
        "2. **Optimize Embeddings:**",
        "   - Use quality embedding models (sentence-transformers ✅)",
        "   - Normalize embeddings for cosine similarity",
        "   - Combine relevant text fields (subject + description ✅)",
        "",
        "3. **Efficient Data Loading:**",
        "   - Use batch processing for large datasets ✅",
        "   - Include rich metadata for filtering ✅",
        "   - Use meaningful document IDs",
        "",
        "4. **Query Optimization:**",
        "   - Use where filters to narrow search space",
        "   - Limit n_results to reasonable numbers (5-10)",
        "   - Include only needed fields in results",
        "",
        "5. **Performance Tips:**",
        "   - Use persistent client for production ✅",
        "   - Set appropriate HNSW parameters",
        "   - Monitor memory usage with large collections",
        "",
        "6. **Error Handling:**",
        "   - Handle collection not found exceptions ✅",
        "   - Validate input data before adding",
        "   - Use try-catch for network operations ✅"
    ]
    
    for practice in practices:
        print(practice)

def test_your_rag_system():
    """Test your actual RAG system"""
    print("🧪 Testing Your RAG System")
    print("=" * 40)
    
    try:
        from rag_service import get_rag_service
        
        rag = get_rag_service()
        
        # Test search
        query = "login problem"
        results = rag.search_similar_tickets(query, max_results=3)
        
        print(f"Search query: '{query}'")
        print(f"Results found: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Ticket {result['ticket_id']}")
            print(f"   Subject: {result['subject']}")
            print(f"   Similarity: {result['similarity_score']:.1%}")
            print(f"   Type: {result['ticket_type']}")
        
        # Get database stats
        stats = rag.get_database_stats()
        print(f"\n📊 Database Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except ImportError:
        print("❌ RAG service not available. Make sure to run from your project directory.")
    except Exception as e:
        print(f"❌ Error testing RAG system: {e}")

if __name__ == "__main__":
    print("📚 ChromaDB Complete Tutorial")
    print("=" * 50)
    
    try:
        # Run all examples
        basic_chromadb_usage()
        persistent_chromadb()
        advanced_chromadb_features()
        your_project_rag_usage()
        chromadb_best_practices()
        test_your_rag_system()
        
        print("\n🎉 Tutorial Complete!")
        print("\n🔧 Next Steps:")
        print("1. Install ChromaDB: pip install chromadb")
        print("2. Run this tutorial: python chromadb_tutorial.py")
        print("3. Initialize your RAG system: python test_rag_feature.py")
        print("4. Start your app and test the RAG search feature")
        
    except Exception as e:
        print(f"❌ Tutorial error: {e}")
        print("💡 Make sure to install: pip install chromadb sentence-transformers") 