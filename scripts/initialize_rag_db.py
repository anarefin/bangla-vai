#!/usr/bin/env python3
"""
Standalone ChromaDB Initialization Script
Run this script once to initialize the RAG database with customer support tickets
"""

import os
import sys
import time
from pathlib import Path

# Add src directory to Python path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🚀 ChromaDB Initialization Script")
    print("=" * 50)
    
    # Set up file paths using the new structure
    csv_path = project_root / "data" / "sample_data" / "customer_support_tickets.csv"
    
    # Check if CSV file exists in the new location
    if not csv_path.exists():
        print(f"❌ Error: customer_support_tickets.csv not found!")
        print(f"💡 Expected location: {csv_path}")
        print(f"📂 Current directory: {os.getcwd()}")
        print(f"📁 Project root: {project_root}")
        
        # Check if it exists in old location
        old_csv_path = project_root / "customer_support_tickets.csv"
        if old_csv_path.exists():
            print(f"✅ Found CSV in old location: {old_csv_path}")
            print("📦 Moving to new location...")
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            old_csv_path.rename(csv_path)
            print(f"✅ Moved to: {csv_path}")
        else:
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
    file_size_mb = csv_path.stat().st_size / (1024 * 1024)
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
        # Import from the new modular structure
        from bangla_vai.services.rag_service import RAGService
        
        # Create RAG service instance
        rag = RAGService()
        print("✅ RAG service created")
        
        # Get current database stats
        try:
            stats = rag.get_database_stats()
            current_count = stats.get("total_tickets", 0)
            print(f"📊 Current database has {current_count} tickets")
            
            if current_count > 0:
                choice = input(f"\n⚠️ Database already has {current_count} tickets. Reinitialize? (y/N): ").lower().strip()
                if choice != 'y':
                    print("✅ Using existing database")
                    return True
        except Exception as e:
            print(f"⚠️ Could not get database stats: {e}")
            print("📝 Proceeding with initialization...")
        
        # Initialize database with the correct CSV path
        print(f"\n🔄 Loading {total_rows:,} tickets into ChromaDB...")
        print("⏳ This will take 2-3 minutes. Please wait...")
        
        start_time = time.time()
        
        try:
            # Pass the CSV path to the initialization method
            count = rag.initialize_database(str(csv_path))
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n🎉 SUCCESS!")
            print(f"✅ Loaded {count:,} tickets into ChromaDB")
            print(f"⏱️ Time taken: {duration:.1f} seconds")
            print(f"💾 Database saved to: {project_root}/data/databases/chroma/")
            
            # Test search functionality
            print(f"\n🧪 Testing search functionality...")
            test_results = rag.search_similar_tickets("login problem", max_results=3)
            
            if test_results:
                print(f"✅ Search test successful! Found {len(test_results)} similar tickets")
                print("\n📋 Sample results:")
                for i, result in enumerate(test_results[:2], 1):
                    similarity = result.get('similarity_score', result.get('score', 0))
                    ticket_id = result.get('ticket_id', result.get('id', 'N/A'))
                    subject = result.get('subject', result.get('title', 'N/A'))
                    print(f"  {i}. Ticket {ticket_id}: {subject} (similarity: {similarity:.1%})")
            else:
                print("⚠️ Search test returned no results")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {str(e)}")
            print("\n🔍 Troubleshooting tips:")
            print("1. Make sure you have enough disk space (need ~100MB)")
            print("2. Check if you have write permissions in current directory")
            print("3. Ensure no other process is using the ChromaDB")
            print("4. Try deleting existing ChromaDB directory and retry")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import RAG service: {e}")
        print("💡 Make sure the project structure is correct and dependencies are installed")
        print(f"🔍 Trying to import from: {src_dir}")
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
            print("1. Start FastAPI server: python run_api.py")
            print("2. Start Streamlit app: streamlit run run_streamlit.py")
            print("3. Or start both: python run_app.py")
            print("4. Go to Voice + Attachment tab")
            print("5. Create tickets and test RAG search")
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