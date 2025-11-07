# tests/test_orchestrator.py
import unittest
import asyncio
import os
import sys
from types import SimpleNamespace

# Ensure src is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from saraphina.orchestrator import SaraphinaOrchestrator, SourceCandidate


class DummyMind:
    async def remember(self, category, text, _internal=False):
        return None

class DummyRobots:
    async def allowed(self, session, url):
        return True

class DummyEngine:
    def __init__(self):
        self.mind = DummyMind()
        self.robots = DummyRobots()
        self.enqueued = []

    async def enqueue_urls(self, pairs, mirrors=None, sha256=None):
        self.enqueued.extend(pairs)
        return len(pairs)

class DummyCurriculum:
    def add_xp_for_interaction(self, query, response, query_type):
        return None

class DummyTorrent:
    def __init__(self, will_start=True):
        self.will_start = will_start
        self.last = None

    async def try_magnet(self, magnet_url: str, timeout_sec: int = 25) -> bool:
        self.last = magnet_url
        return self.will_start


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = DummyEngine()
        self.knowledge = object()
        self.curriculum = DummyCurriculum()
        cfg = {"providers": [], "fallback_on_magnet_fail": True}
        self.orch = SaraphinaOrchestrator(self.engine, self.knowledge, self.curriculum, cfg)
        # monkeypatch torrent
        self.orch.torrent = DummyTorrent(will_start=False)

    async def test_candidate_formatting_and_choice_direct(self):
        # Inject candidates directly
        self.orch._last_candidates = [
            SourceCandidate(title="Direct Pack", type="direct", url="https://example.com", urls=["https://x/a.zip", "https://x/b.zip"]) 
        ]
        # Choose index 1
        msg = await self.orch.proceed_with_choice(1)
        self.assertIn("Enqueued 2", msg)
        self.assertEqual(len(self.engine.enqueued), 2)

    async def test_magnet_fallback_to_direct(self):
        # magnet fails (will_start=False), then fallback to direct URLs in same candidate
        self.orch._last_candidates = [
            SourceCandidate(title="Magnet Fallback", type="magnet", url="magnet:?xt=urn:btih:abc", urls=["magnet:?xt=urn:btih:abc", "https://x/file1.zip"]) 
        ]
        msg = await self.orch.proceed_with_choice(1)
        self.assertIn("Enqueued 1", msg)
        self.assertEqual(len(self.engine.enqueued), 1)

    async def test_handle_request_empty(self):
        # No providers => no results string
        txt = await self.orch.handle_request("download something")
        self.assertIn("No results", txt)


if __name__ == '__main__':
    unittest.main()
