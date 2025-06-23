"""
RAG (Retrieval Augmented Generation) Service
Provides vector-based similarity search for customer support tickets using ChromaDB
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging
from pathlib import Path
import threading
import time
from functools import lru_cache

# Import configuration
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread lock for singleton pattern
_lock = threading.Lock()


class RAGService:
    """RAG Service for vector-based ticket similarity search using ChromaDB with singleton pattern"""
    
    _instance: Optional['RAGService'] = None
    _initialized: bool = False
    
    def __new__(cls, csv_file_path: Optional[str] = None):
        """Singleton pattern to prevent multiple instances"""
        with _lock:
            if cls._instance is None:
                cls._instance = super(RAGService, cls).__new__(cls)
            return cls._instance
    
    def __init__(self, csv_file_path: Optional[str] = None):
        # Only initialize once
        if RAGService._initialized:
            return
            
        # Use default path from configuration if not provided
        if csv_file_path is None:
            # Fix: Use current working directory as project root and build path
            project_root = Path.cwd()
            csv_file_path = str(project_root / "data" / "sample_data" / "customer_support_tickets.csv")
        
        self.csv_file_path = csv_file_path
        self.collection_name = "customer_support_tickets"
        
        logger.info("Initializing ChromaDB RAG Service with singleton pattern...")
        logger.info(f"Using CSV file path: {self.csv_file_path}")
        
        # Initialize sentence transformer model with caching
        self.encoder = self._get_sentence_transformer()
        
        # Initialize ChromaDB client
        self._initialize_chromadb()
        
        RAGService._initialized = True
        logger.info("ChromaDB RAG Service initialized successfully")
    
    @lru_cache(maxsize=1)
    def _get_sentence_transformer(self) -> SentenceTransformer:
        """Cache the sentence transformer model to avoid repeated loading"""
        logger.info("Loading sentence transformer model (cached)...")
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection"""
        try:
            # Use configured ChromaDB path - make it absolute
            chroma_path = Path(settings.CHROMA_DB_PATH).resolve()
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initializing ChromaDB at: {chroma_path}")
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    persist_directory=str(chroma_path)
                )
            )
            
            # Get or create collection with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.collection = self.chroma_client.get_collection(name=self.collection_name)
                    count = self.collection.count()
                    logger.info(f"Loaded existing ChromaDB collection '{self.collection_name}' with {count} tickets")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Last attempt - try to create new collection
                        try:
                            self.collection = self.chroma_client.create_collection(
                                name=self.collection_name,
                                metadata={"hnsw:space": "cosine"}
                            )
                            logger.info(f"Created new ChromaDB collection '{self.collection_name}'")
                        except Exception as create_error:
                            logger.error(f"Failed to create ChromaDB collection: {create_error}")
                            raise
                    else:
                        logger.warning(f"Failed to load collection (attempt {attempt + 1}): {e}")
                        time.sleep(0.5)  # Brief pause before retry
                        
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def initialize_database(self, csv_file_path: Optional[str] = None) -> int:
        """
        Initialize the ChromaDB vector database with tickets from CSV file
        Returns the number of tickets loaded
        """
        try:
            # Use provided path or fall back to instance path
            csv_path = csv_file_path or self.csv_file_path
            
            # Check if CSV file exists
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            # Load CSV data
            logger.info(f"Loading tickets from {csv_path}...")
            df = pd.read_csv(csv_path)
            
            # Clean and prepare data
            initial_count = len(df)
            df = df.dropna(subset=['Ticket Subject', 'Ticket Description'])
            logger.info(f"Cleaned data: {initial_count} → {len(df)} tickets")
            
            # Combine relevant text fields for embedding
            df['combined_text'] = (
                df['Ticket Subject'].astype(str) + ' ' +
                df['Ticket Description'].astype(str) + ' ' +
                df['Ticket Type'].fillna('').astype(str) + ' ' +
                df['Product Purchased'].fillna('').astype(str)
            )
            
            # Clear existing collection data
            try:
                self.chroma_client.delete_collection(name=self.collection_name)
                logger.info("Cleared existing ChromaDB collection")
            except:
                pass
            
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Process in batches to avoid memory issues
            batch_size = 100
            total_processed = 0
            
            logger.info(f"Processing {len(df)} tickets in batches of {batch_size}...")
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                # Generate embeddings for batch
                texts = batch_df['combined_text'].tolist()
                try:
                    embeddings = self.encoder.encode(texts, show_progress_bar=False, batch_size=32)
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}: {e}")
                    continue
                
                # Prepare metadata
                metadatas = []
                for _, row in batch_df.iterrows():
                    try:
                        metadata = {
                            'ticket_id': str(row['Ticket ID']),
                            'customer_name': str(row['Customer Name']),
                            'customer_email': str(row['Customer Email']),
                            'subject': str(row['Ticket Subject']),
                            'description': str(row['Ticket Description']),
                            'ticket_type': str(row['Ticket Type']),
                            'product': str(row['Product Purchased']),
                            'status': str(row['Ticket Status']),
                            'priority': str(row['Ticket Priority']),
                            'channel': str(row['Ticket Channel']),
                            'resolution': str(row.get('Resolution', '')),
                            'satisfaction_rating': str(row.get('Customer Satisfaction Rating', '')) if pd.notna(row.get('Customer Satisfaction Rating')) else ''
                        }
                        metadatas.append(metadata)
                    except Exception as e:
                        logger.warning(f"Error processing row metadata: {e}")
                        continue
                
                # Create document IDs
                ids = [f"ticket_{row['Ticket ID']}" for _, row in batch_df.iterrows()]
                
                # Add to ChromaDB collection
                try:
                    self.collection.add(
                        embeddings=embeddings.tolist(),
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
                    total_processed += len(batch_df)
                    logger.info(f"Processed {total_processed}/{len(df)} tickets...")
                except Exception as e:
                    logger.error(f"Failed to add batch to ChromaDB: {e}")
                    continue
            
            logger.info(f"Successfully initialized ChromaDB with {total_processed} tickets")
            return total_processed
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB database: {str(e)}")
            raise
    
    def search_similar_tickets(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar tickets using ChromaDB vector similarity
        
        Args:
            query: Search query (could be a problem description, keywords, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of similar tickets with similarity scores
        """
        try:
            # Validate inputs
            if not query or not query.strip():
                logger.warning("Empty query provided")
                return []
                
            max_results = max(1, min(max_results, 20))  # Limit between 1-20
            
            # Ensure we have a valid collection
            if not hasattr(self, 'collection') or self.collection is None:
                logger.warning("Collection not initialized, attempting to reinitialize...")
                try:
                    self.collection = self.chroma_client.get_collection(name=self.collection_name)
                    logger.info(f"Reloaded collection '{self.collection_name}'")
                except Exception as e:
                    logger.error(f"Failed to reload collection: {e}")
                    raise RuntimeError("ChromaDB not properly initialized")
            
            # Check if collection has data
            try:
                count = self.collection.count()
                if count == 0:
                    logger.warning("ChromaDB collection is empty")
                    return []
            except Exception as e:
                logger.error(f"Error checking collection count: {e}")
                # Continue with search attempt
            
            # Generate embedding for the query
            try:
                query_embedding = self.encoder.encode([query.strip()])
            except Exception as e:
                logger.error(f"Failed to encode query: {e}")
                return []
            
            # Search in ChromaDB
            try:
                results = self.collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=max_results,
                    include=['documents', 'metadatas', 'distances']
                )
            except Exception as e:
                logger.error(f"ChromaDB query failed: {e}")
                return []
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    try:
                        # Convert distance to similarity score
                        similarity_score = max(0, 1 - results['distances'][0][i])
                        
                        # Only include results above minimum similarity threshold
                        if similarity_score > 0.1:
                            result = {
                                'id': results['ids'][0][i],
                                'similarity_score': similarity_score,
                                'ticket_id': results['metadatas'][0][i].get('ticket_id', 'unknown'),
                                'subject': results['metadatas'][0][i].get('subject', 'No subject'),
                                'description': results['metadatas'][0][i].get('description', 'No description'),
                                'ticket_type': results['metadatas'][0][i].get('ticket_type', 'unknown'),
                                'product': results['metadatas'][0][i].get('product', 'unknown'),
                                'status': results['metadatas'][0][i].get('status', 'unknown'),
                                'priority': results['metadatas'][0][i].get('priority', 'unknown'),
                                'resolution': results['metadatas'][0][i].get('resolution', 'No resolution'),
                                'customer_satisfaction': results['metadatas'][0][i].get('satisfaction_rating', ''),
                                'combined_text': results['documents'][0][i] if results['documents'] and results['documents'][0] else 'No text'
                            }
                            formatted_results.append(result)
                    except Exception as e:
                        logger.warning(f"Error formatting result {i}: {e}")
                        continue
            
            logger.info(f"ChromaDB search for '{query[:50]}...' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar tickets: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get ChromaDB database statistics"""
        try:
            count = self.collection.count() if hasattr(self, 'collection') and self.collection else 0
            
            # Get ChromaDB directory size
            chroma_path = Path("./chroma_db")
            db_size_mb = 0
            if chroma_path.exists():
                db_size_mb = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file()) / (1024 * 1024)
            
            return {
                "total_tickets": count,
                "collection_name": self.collection_name,
                "encoder_model": "all-MiniLM-L6-v2",
                "database_path": "./chroma_db",
                "database_size_mb": round(db_size_mb, 2),
                "singleton_initialized": RAGService._initialized,
                "database_type": "ChromaDB"
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}


# Global RAG service instance getter with singleton pattern
def get_rag_service() -> RAGService:
    """Get or create the ChromaDB RAG service instance with singleton pattern"""
    try:
        return RAGService()
    except Exception as e:
        logger.error(f"Failed to get ChromaDB RAG service: {e}")
        raise

# Alias for compatibility during transition
def get_chromadb_rag_service() -> RAGService:
    """Alias for getting ChromaDB RAG service"""
    return get_rag_service()


if __name__ == "__main__":
    # Test the RAG service
    rag = RAGService()
    
    # Initialize database
    print("Initializing RAG database...")
    count = rag.initialize_database()
    print(f"Loaded {count} tickets")
    
    # Test search
    print("\nTesting search...")
    results = rag.search_similar_tickets("login problem", max_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Ticket ID: {result['ticket_id']}")
        print(f"Subject: {result['subject']}")
        print(f"Similarity: {result['similarity_score']:.3f}")
        print(f"Description: {result['description'][:100]}...") 