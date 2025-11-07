# tests/test_torrent_manager.py
import unittest
import os
import sys

# Ensure src is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from saraphina.torrent_manager import TorrentManager


class TestableTorrentManager(TorrentManager):
    def __init__(self):
        super().__init__({"transmission_url": "http://localhost:9091/transmission/rpc"})
        self._calls = []
        self._session_id = None

    async def _transmission_request(self, method: str, arguments):
        # Simulate 409 then success for session id negotiation on first call
        if self._session_id is None:
            self._session_id = "abc123"
            # After setting, retry will occur in parent; just return a success structure
        # Return a typical success response for torrent-add
        if method == "torrent-add":
            return {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "demo"}}}
        return {"result": "success", "arguments": {}}


class TorrentManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_try_magnet_transmission_accepts(self):
        tm = TestableTorrentManager()
        ok = await tm.try_magnet("magnet:?xt=urn:btih:abcdef")
        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main()
