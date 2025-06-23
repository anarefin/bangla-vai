#!/usr/bin/env python3
"""
RAG Database Status Checker
Quick script to check if ChromaDB is properly initialized
"""

import os
import sys

def check_rag_status():
    """Check RAG database status"""
    print("🔍 RAG Database Status Check")
    print("=" * 40)
    
    # Check if ChromaDB directory exists
    chroma_path = "./chroma_db"
    if os.path.exists(chroma_path):
        print(f"✅ ChromaDB directory found: {chroma_path}")
        
        # Get directory size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(chroma_path):
            for filename in filenames:
                fp = os.path.join(dirpath, filename)
                total_size += os.path.getsize(fp)
        
        size_mb = total_size / (1024 * 1024)
        print(f"📊 Database size: {size_mb:.1f} MB")
    else:
        print(f"❌ ChromaDB directory not found: {chroma_path}")
        print("💡 Run: python initialize_rag_db.py")
        return False
    
    # Try to connect to RAG service
    try:
        from rag_service import get_rag_service
        
        rag = get_rag_service()
        stats = rag.get_database_stats()
        
        ticket_count = stats.get("total_tickets", 0)
        print(f"📈 Total tickets in database: {ticket_count:,}")
        
        if ticket_count == 0:
            print("⚠️ Database is empty!")
            print("💡 Run: python initialize_rag_db.py")
            return False
        elif ticket_count < 29000:
            print("⚠️ Database seems incomplete (expected ~29,808 tickets)")
            print("💡 Consider reinitializing: python initialize_rag_db.py")
        else:
            print("✅ Database looks complete!")
        
        # Test search functionality
        print("\n🧪 Testing search functionality...")
        results = rag.search_similar_tickets("login problem", max_results=2)
        
        if results:
            print(f"✅ Search test successful! Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Ticket {result['ticket_id']}: {result['subject']} (similarity: {result['similarity_score']:.1%})")
        else:
            print("❌ Search test failed - no results returned")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to RAG service: {e}")
        return False

def check_fastapi_rag_endpoints():
    """Check if FastAPI RAG endpoints are working"""
    print("\n🌐 FastAPI RAG Endpoints Check")
    print("-" * 35)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Check health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI server is running")
            else:
                print(f"⚠️ FastAPI server responded with: {response.status_code}")
        except:
            print("❌ FastAPI server is not running")
            print("💡 Start server: python fastapi_app.py")
            return False
        
        # Test RAG search endpoint
        try:
            response = requests.post(
                f"{base_url}/rag/search",
                data={"query": "test search", "max_results": 1},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RAG search endpoint working")
                print(f"📊 Search returned {result.get('total_results', 0)} results")
            else:
                print(f"❌ RAG search endpoint error: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ RAG search endpoint error: {e}")
            return False
        
        return True
        
    except ImportError:
        print("❌ requests library not available")
        return False

if __name__ == "__main__":
    print("🎫 Bangla Vai - RAG Status Checker")
    print("=" * 50)
    
    # Check local RAG database
    rag_ok = check_rag_status()
    
    # Check FastAPI endpoints
    api_ok = check_fastapi_rag_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"🗄️ RAG Database: {'✅ OK' if rag_ok else '❌ Issues'}")
    print(f"🌐 FastAPI Endpoints: {'✅ OK' if api_ok else '❌ Issues'}")
    
    if rag_ok and api_ok:
        print("\n🎉 All systems ready! You can use RAG search in Streamlit.")
    else:
        print("\n🔧 Fix the issues above before using RAG search.")
        
        if not rag_ok:
            print("1. Run: python initialize_rag_db.py")
        if not api_ok:
            print("2. Start FastAPI: python fastapi_app.py")
    
    sys.exit(0 if (rag_ok and api_ok) else 1) 