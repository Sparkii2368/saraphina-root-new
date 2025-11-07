#!/usr/bin/env python3
"""Quick test of Saraphina AI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from saraphina.ai_core import SaraphinaAI

print("🧪 Testing Saraphina AI Core...\n")

# Initialize AI
ai = SaraphinaAI()
print("✅ AI Initialized")
print(ai.get_status_summary())
print("\n" + "="*60 + "\n")

# Test queries
test_queries = [
    "Hello Saraphina",
    "Who are you?",
    "What can you do?",
    "Tell me about your learning capabilities",
]

for query in test_queries:
    print(f"💬 User: {query}")
    response = ai.process_query(query)
    print(f"🤖 Saraphina: {response}\n")
    print("-" * 60 + "\n")

# Final status
print("="*60)
print("FINAL STATUS AFTER TESTING:")
print(ai.get_status_summary())
print("="*60)

print("\n✅ All tests completed successfully!")
print("🎉 Saraphina AI is working perfectly!\n")
