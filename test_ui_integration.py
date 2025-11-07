#!/usr/bin/env python3
"""
Quick test to verify UI is integrated correctly
"""

import sys
import os

# Check if UI modules are importable
try:
    from saraphina.ui_manager import SaraphinaUI
    from saraphina.ui_live import LiveUIContext
    print("✅ UI modules imported successfully")
except Exception as e:
    print(f"❌ UI import failed: {e}")
    sys.exit(1)

# Check if UI can be initialized
try:
    ui = SaraphinaUI()
    if ui.enabled:
        print("✅ UI initialized and Rich is available")
    else:
        print("⚠️  UI initialized but Rich not available (will use fallback)")
except Exception as e:
    print(f"❌ UI initialization failed: {e}")
    sys.exit(1)

# Check if main terminal file has UI integration
try:
    with open('saraphina_terminal_ultra.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    checks = [
        ('ui_manager import', 'from saraphina.ui_manager import' in content or 'SaraphinaUI' in content),
        ('UI initialization', 'ui = SaraphinaUI()' in content or 'SaraphinaUI()' in content),
        ('UI message handling', 'ui.add_message' in content),
        ('UI voice indicator', 'ui.set_speaking' in content),
        ('UI context', 'ui_ctx' in content or 'LiveUIContext' in content)
    ]
    
    print("\n📋 Integration checklist:")
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    
    all_passed = all(passed for _, passed in checks)
    if all_passed:
        print("\n✅ All integration checks passed!")
        print("\n🚀 To enable futuristic UI:")
        print("   1. Set environment variable: SARAPHINA_UI_MODE=futuristic")
        print("   2. Or run: python demo_ui.py (standalone preview)")
    else:
        print("\n⚠️  Some checks failed - UI may not be fully integrated")
        
except Exception as e:
    print(f"❌ Integration check failed: {e}")
    sys.exit(1)

print("\n✅ UI integration test complete!")
