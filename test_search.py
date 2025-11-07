#!/usr/bin/env python3
import sys, asyncio
sys.path.insert(0, r'D:\Saraphina Root\src')
from saraphina.orchestrator import SaraphinaOrchestrator
from saraphina.downloader_engine import SaraphinaEngine
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.curriculum_engine import CurriculumEngine

async def main():
    ke = KnowledgeEngine()
    ce = CurriculumEngine()
    en = SaraphinaEngine(ke, ce)
    cfg = {
        'providers': [{'type': 'web_search', 'top_n': 3, 'fetch_links': True}],
        'auto_choose': False
    }
    orch = SaraphinaOrchestrator(en, ke, ce, cfg)
    txt = await orch.handle_request('ubuntu iso')
    print(txt)
    print('\nTop candidates:')
    for i, c in enumerate(orch._last_candidates[:3], 1):
        print(i, c.type, c.url)

if __name__ == '__main__':
    asyncio.run(main())
