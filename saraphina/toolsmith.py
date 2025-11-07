#!/usr/bin/env python3
"""
Toolsmith - proposes and builds small utilities using FeatureFactory and the sandbox.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .feature_factory import FeatureFactory

class Toolsmith:
    def __init__(self, author: str = "toolsmith", db_path: Optional[str] = None):
        self.ff = FeatureFactory(db_path=db_path, author=author)

    def _make_code(self, description: str) -> str:
        d = description.lower()
        # API wrapper template
        if 'api' in d and ('wrapper' in d or 'client' in d):
            return (
                "import requests, json\n"
                "def call_api(endpoint: str, method='GET', data=None):\n"
                "    url = 'https://api.example.com' + endpoint\n"
                "    r = requests.request(method, url, json=data, timeout=10)\n"
                "    return r.json() if r.ok else {'error': r.status_code}\n"
                "if __name__=='__main__':\n"
                "    import sys; print(json.dumps(call_api(sys.argv[1] if len(sys.argv)>1 else '/status')))\n"
            )
        # Log parser template
        if 'log' in d and ('pars' in d or 'analy' in d):
            return (
                "import re, json\n"
                "def parse_log(path: str):\n"
                "    with open(path,'r') as f: lines = f.readlines()\n"
                "    errors = [l for l in lines if 'ERROR' in l or 'WARN' in l]\n"
                "    return {'total': len(lines), 'errors': len(errors), 'sample': errors[:10]}\n"
                "if __name__=='__main__':\n"
                "    import sys; print(json.dumps(parse_log(sys.argv[1] if len(sys.argv)>1 else 'app.log')))\n"
            )
        # CSV processor
        if 'csv' in d or 'spreadsheet' in d:
            return (
                "import csv, json\n"
                "def process_csv(path: str):\n"
                "    with open(path, 'r', encoding='utf-8') as f:\n"
                "        reader = csv.DictReader(f)\n"
                "        rows = list(reader)\n"
                "    return {'count': len(rows), 'sample': rows[:5]}\n"
                "if __name__=='__main__':\n"
                "    import sys; print(json.dumps(process_csv(sys.argv[1] if len(sys.argv)>1 else 'data.csv')))\n"
            )
        # JSON transformer
        if 'json' in d and ('transform' in d or 'convert' in d):
            return (
                "import json\n"
                "def transform_json(data: dict):\n"
                "    # Example: flatten nested keys\n"
                "    flat = {}\n"
                "    for k, v in data.items():\n"
                "        if isinstance(v, dict):\n"
                "            for sk, sv in v.items(): flat[f'{k}_{sk}'] = sv\n"
                "        else: flat[k] = v\n"
                "    return flat\n"
                "if __name__=='__main__':\n"
                "    import sys; d = json.load(open(sys.argv[1])) if len(sys.argv)>1 else {'a':1}; print(json.dumps(transform_json(d)))\n"
            )
        if 'list backups' in d or 'backups' in d:
            return (
                "import os, json\n"
                "from pathlib import Path\n"
                "def main():\n"
                "    root = Path('ai_data')/ 'backups'\n"
                "    root.mkdir(parents=True, exist_ok=True)\n"
                "    files = [str(p) for p in root.glob('*') if p.is_file()]\n"
                "    print(json.dumps({'count': len(files), 'files': files}))\n"
                "if __name__=='__main__': main()\n"
            )
        if 'search facts' in d:
            return (
                "import json\n"
                "from saraphina.knowledge_engine import KnowledgeEngine\n"
                "def run(q: str):\n"
                "    ke = KnowledgeEngine()\n"
                "    hits = ke.recall(q, top_k=5, threshold=0.5)\n"
                "    return [{'id': h['id'], 'summary': (h.get('summary') or '')[:120]} for h in hits]\n"
                "if __name__=='__main__':\n"
                "    import sys; q = ' '.join(sys.argv[1:]) or 'backup'; print(json.dumps(run(q)))\n"
            )
        # default utility template
        return (
            "def tool(input_text: str) -> str:\n"
            "    # Echo utility with basic transform\n"
            "    return input_text.strip().upper()\n"
            "if __name__=='__main__':\n"
            "    import sys; print(tool(' '.join(sys.argv[1:])))\n"
        )

    def propose_and_build(self, description: str) -> Dict[str, Any]:
        code = self._make_code(description)
        tests: List[Dict[str, Any]] = []
        if 'tool(' in code:
            tests = [{"inputs": {"input_text": "hello"}, "expected": "HELLO"}]
        elif 'run(q' in code:
            tests = [{"inputs": {}, "expected": True}]  # sandbox compares truthiness for lack of argv
        spec = {"title": description[:60], "code": code, "tests": tests}
        art_id = self.ff.propose_feature(spec)
        report = self.ff.run_sandbox(art_id)
        return {"artifact_id": art_id, "report": report}
