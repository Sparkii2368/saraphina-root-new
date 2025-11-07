#!/usr/bin/env python3
"""
Quick test to verify OpenAI GPT-4 integration for Saraphina's autonomous research.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv('D:\\Saraphina Root\\.env')

def test_api_key():
    """Test if OpenAI API key is loaded."""
    print("\n" + "="*70)
    print("TEST 1: OpenAI API Key Configuration")
    print("="*70)
    
    key = os.getenv('OPENAI_API_KEY')
    
    if key:
        print(f"✅ API Key loaded successfully")
        print(f"   Prefix: {key[:20]}...")
        print(f"   Suffix: ...{key[-10:]}")
        return True
    else:
        print("❌ API Key not found in environment")
        return False


def test_openai_connection():
    """Test basic OpenAI API connection."""
    print("\n" + "="*70)
    print("TEST 2: OpenAI API Connection")
    print("="*70)
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("📡 Testing connection to OpenAI API...")
        
        # Simple test query
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, Saraphina is ready to learn!' in one sentence."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        
        print(f"✅ Connection successful!")
        print(f"   Response: {result}")
        print(f"   Model: {response.model}")
        print(f"   Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except ImportError:
        print("⚠️  OpenAI library not installed")
        print("   Install with: pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_research_agent():
    """Test ResearchAgent with GPT-4 backend."""
    print("\n" + "="*70)
    print("TEST 3: ResearchAgent GPT-4 Integration")
    print("="*70)
    
    try:
        from saraphina.db import init_db
        from saraphina.research_agent import ResearchAgent
        from saraphina.knowledge_engine import KnowledgeEngine
        
        # Use in-memory database for testing
        conn = init_db(':memory:')
        ke = KnowledgeEngine(conn)
        research = ResearchAgent(conn, ke)
        
        print("🔍 Testing research on 'photosynthesis' (limited to 3 facts)...")
        
        # Run research with minimal facts to save costs
        report = research.research(
            topic='photosynthesis',
            allow_web=False,
            use_gpt4=True,
            recursive_depth=1,  # Minimal depth
            max_facts=3,        # Only 3 facts for testing
            store_facts=True
        )
        
        if report.get('gpt4_facts'):
            print(f"✅ Research successful!")
            print(f"   Facts discovered: {len(report['gpt4_facts'])}")
            print(f"   Facts stored in KB: {report['fact_count']}")
            print(f"\n   Sample facts:")
            for i, fact in enumerate(report['gpt4_facts'][:3], 1):
                print(f"   {i}. {fact[:80]}...")
            
            # Verify storage
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM facts")
            stored_count = cur.fetchone()[0]
            print(f"\n   Verified: {stored_count} facts in database")
            
            return True
        else:
            print("⚠️  No facts discovered (but no errors)")
            return True
            
    except ImportError as e:
        print(f"⚠️  Module import error: {e}")
        print("   Make sure Saraphina modules are available")
        return False
        
    except Exception as e:
        print(f"❌ Research test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all GPT-4 integration tests."""
    print("\n" + "🧪 " + "="*66 + " 🧪")
    print("   SARAPHINA GPT-4 INTEGRATION TEST SUITE")
    print("🧪 " + "="*66 + " 🧪")
    
    results = []
    
    # Test 1: API Key
    results.append(test_api_key())
    
    # Test 2: Connection (only if API key is loaded)
    if results[0]:
        results.append(test_openai_connection())
    else:
        print("\n⏭️  Skipping connection test (no API key)")
        results.append(False)
    
    # Test 3: ResearchAgent (only if connection works)
    if results[1]:
        results.append(test_research_agent())
    else:
        print("\n⏭️  Skipping ResearchAgent test (connection failed)")
        results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    test_names = ["API Key Configuration", "OpenAI Connection", "ResearchAgent Integration"]
    
    for i, (name, passed) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{i}. {name:30s} {status}")
    
    all_passed = all(results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nSaraphina's GPT-4 autonomous research is ready!")
        print("\nNext steps:")
        print("  1. Start terminal: python saraphina_terminal_ultra.py")
        print("  2. Try: /research artificial intelligence")
        print("  3. Try: /research quantum computing")
        print("  4. Check stored knowledge: /kb")
        print()
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease check:")
        print("  - OpenAI API key is valid")
        print("  - Internet connection is active")
        print("  - OpenAI library is installed: pip install openai")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
