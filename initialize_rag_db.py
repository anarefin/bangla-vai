#!/usr/bin/env python3
"""
Standalone ChromaDB Initialization Script
Run this script once to initialize the RAG database with customer support tickets
"""

import os
import sys
import time
from pathlib import Path

def main():
    print("🚀 ChromaDB Initialization Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("customer_support_tickets.csv"):
        print("❌ Error: customer_support_tickets.csv not found!")
        print("💡 Make sure you're running this script from the project directory")
        print("📂 Current directory:", os.getcwd())
        return False
    
    # Check if requirements are installed
    try:
        print("📦 Checking dependencies...")
        import chromadb
        import pandas as pd
        from sentence_transformers import SentenceTransformer
        print("✅ All dependencies are available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Please install requirements: pip install -r requirements.txt")
        return False
    
    # Check CSV file size
    csv_path = "customer_support_tickets.csv"
    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"📊 CSV file size: {file_size_mb:.1f} MB")
    
    # Get number of rows
    try:
        df_sample = pd.read_csv(csv_path, nrows=1)
        total_rows = sum(1 for _ in open(csv_path)) - 1  # Subtract header
        print(f"📈 Total tickets in CSV: {total_rows:,}")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Initialize RAG service
    print("\n🤖 Initializing RAG Service...")
    try:
        from rag_service import RAGService
        
        # Create RAG service instance
        rag = RAGService()
        print("✅ RAG service created")
        
        # Get current database stats
        stats = rag.get_database_stats()
        current_count = stats.get("total_tickets", 0)
        print(f"📊 Current database has {current_count} tickets")
        
        if current_count > 0:
            choice = input(f"\n⚠️ Database already has {current_count} tickets. Reinitialize? (y/N): ").lower().strip()
            if choice != 'y':
                print("✅ Using existing database")
                return True
        
        # Initialize database
        print(f"\n🔄 Loading {total_rows:,} tickets into ChromaDB...")
        print("⏳ This will take 2-3 minutes. Please wait...")
        
        start_time = time.time()
        
        try:
            count = rag.initialize_database()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n🎉 SUCCESS!")
            print(f"✅ Loaded {count:,} tickets into ChromaDB")
            print(f"⏱️ Time taken: {duration:.1f} seconds")
            print(f"💾 Database saved to: ./chroma_db/")
            
            # Test search functionality
            print(f"\n🧪 Testing search functionality...")
            test_results = rag.search_similar_tickets("login problem", max_results=3)
            
            if test_results:
                print(f"✅ Search test successful! Found {len(test_results)} similar tickets")
                print("\n📋 Sample results:")
                for i, result in enumerate(test_results[:2], 1):
                    print(f"  {i}. Ticket {result['ticket_id']}: {result['subject']} (similarity: {result['similarity_score']:.1%})")
            else:
                print("⚠️ Search test returned no results")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {str(e)}")
            print("\n🔍 Troubleshooting tips:")
            print("1. Make sure you have enough disk space (need ~100MB)")
            print("2. Check if you have write permissions in current directory")
            print("3. Ensure no other process is using the ChromaDB")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import RAG service: {e}")
        print("💡 Make sure rag_service.py exists and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_system_requirements():
    """Check system requirements"""
    print("🔍 System Requirements Check")
    print("-" * 30)
    
    # Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 8):
        print("❌ Python 3.8 or higher required")
        return False
    else:
        print("✅ Python version OK")
    
    # Available disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_mb = free / (1024 * 1024)
        print(f"💾 Available disk space: {free_mb:.0f} MB")
        if free_mb < 200:
            print("⚠️ Warning: Low disk space. Need at least 200MB")
        else:
            print("✅ Disk space OK")
    except:
        print("⚠️ Could not check disk space")
    
    # Memory check (rough estimate)
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        print(f"🧠 Available RAM: {available_gb:.1f} GB")
        if available_gb < 2:
            print("⚠️ Warning: Low memory. Recommend at least 2GB")
        else:
            print("✅ Memory OK")
    except ImportError:
        print("⚠️ Could not check memory (psutil not installed)")
    
    print()
    return True

if __name__ == "__main__":
    print("🎫 Bangla Vai - ChromaDB Initialization")
    print("=" * 50)
    
    try:
        # Check system requirements
        if not check_system_requirements():
            print("❌ System requirements not met")
            sys.exit(1)
        
        # Run initialization
        success = main()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 ChromaDB Initialization Complete!")
            print("\n📋 Next Steps:")
            print("1. Start FastAPI server: python fastapi_app.py")
            print("2. Start Streamlit app: streamlit run streamlit_app.py")
            print("3. Go to Voice + Attachment tab")
            print("4. Create tickets and test RAG search")
            print("\n💡 The ChromaDB is now ready for use!")
        else:
            print("\n❌ Initialization failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 