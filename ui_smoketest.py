#!/usr/bin/env python3
import asyncio, os, sys, traceback
from pathlib import Path

# Ensure src on sys.path
ROOT = Path(__file__).parent.resolve()
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

async def main():
    try:
        from saraphina.ui_app import SaraphinaUI
        ui = SaraphinaUI(port=7071)
        await ui.start()
        # Quick health check
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get('http://127.0.0.1:7071/') as r:
                text = await r.text()
                print('UI_OK', r.status, len(text))
        await ui.stop()
    except Exception as e:
        print('UI_ERR', repr(e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
