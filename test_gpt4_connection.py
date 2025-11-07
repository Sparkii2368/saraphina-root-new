#!/usr/bin/env python3
"""Quick test to verify OpenAI GPT-4 API connectivity."""
import os
import sys
from pathlib import Path

# Load environment variables
env_files = [
    Path(__file__).parent / '.env',
    Path('D:/SaraphinaApp/.env')
]

for env_file in env_files:
    if env_file.exists():
        print(f"Loading {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

api_key = os.getenv('OPENAI_API_KEY')
print(f"\n✓ API key found: {api_key[:20]}...{api_key[-10:]}" if api_key else "✗ No API key found")

if not api_key:
    print("\n❌ OPENAI_API_KEY not found in environment!")
    sys.exit(1)

try:
    from openai import OpenAI
    print("✓ openai package imported")
    
    client = OpenAI(api_key=api_key)
    
    print("\n🔄 Testing GPT-4o connection...")
    response = client.chat.completions.create(
        model="gpt-4o",  # Latest GPT-4o model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello!' in one word."}
        ],
        max_tokens=10
    )
    
    reply = response.choices[0].message.content
    print(f"✅ GPT-4 responded: {reply}")
    print(f"✅ API is working! Model: {response.model}")
    print(f"✅ Tokens used: {response.usage.total_tokens}")
    
except ImportError:
    print("\n❌ openai package not installed!")
    print("Install with: pip install openai")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ API call failed: {e}")
    sys.exit(1)

print("\n🎉 All checks passed! Saraphina can now learn from GPT-4o (latest model).")
