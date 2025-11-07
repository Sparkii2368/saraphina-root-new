#!/usr/bin/env python3
"""
ShadowSync - encrypted shadow nodes, consensus reconciliation, and recovery.
"""
from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from .db import write_audit_log

class ShadowManager:
    def __init__(self, conn, security_manager=None):
        self.conn = conn
        self.sec = security_manager

    def register(self, name: str, path: str, device_id: Optional[str] = None, active: bool = True) -> str:
        sid = f"shadow_{uuid4()}"
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO shadow_nodes (id, name, device_id, path, added_at, active) VALUES (?,?,?,?,?,?)",
            (sid, name, device_id or '', path, datetime.utcnow().isoformat(), 1 if active else 0)
        )
        self.conn.commit()
        write_audit_log(self.conn, 'shadow', 'register', sid, {'name': name, 'path': path})
        Path(path).mkdir(parents=True, exist_ok=True)
        return sid

    def list(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM shadow_nodes WHERE active=1")
        return [dict(r) for r in cur.fetchall()]

    def _checksum(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                b = f.read(8192)
                if not b: break
                h.update(b)
        return h.hexdigest()

    def push_snapshot(self, enc_backup_path: str, sig: Optional[str] = None) -> List[Dict]:
        """Copy an existing encrypted backup .enc (and .sig) to all active shadow nodes."""
        results = []
        for node in self.list():
            try:
                target_dir = Path(node['path'])
                target_dir.mkdir(parents=True, exist_ok=True)
                fname = Path(enc_backup_path).name
                target = target_dir / fname
                # copy file
                data = Path(enc_backup_path).read_bytes()
                target.write_bytes(data)
                # copy signature if provided
                if sig:
                    (target_dir / (fname + '.sig')).write_text(sig, encoding='utf-8')
                results.append({'node': node['name'], 'path': str(target), 'ok': True})
            except Exception as e:
                results.append({'node': node['name'], 'error': str(e), 'ok': False})
        write_audit_log(self.conn, 'shadow', 'push_snapshot', 'all', {'results': results})
        return results

    def inventory(self) -> List[Dict]:
        """List available snapshots on each node with checksums."""
        inv = []
        for node in self.list():
            try:
                p = Path(node['path'])
                files = [f for f in p.glob('*.enc')]
                for f in files:
                    try:
                        inv.append({
                            'node': node['name'],
                            'file': str(f),
                            'ts': f.stat().st_mtime,
                            'checksum': self._checksum(str(f))
                        })
                    except Exception:
                        continue
            except Exception:
                continue
        return inv

    def reconcile(self) -> Dict:
        inv = self.inventory()
        # group by checksum
        groups: Dict[str, List[Dict]] = {}
        for item in inv:
            groups.setdefault(item['checksum'], []).append(item)
        if not groups:
            return {'status': 'no_snapshots'}
        # majority vote by group size; tie -> latest timestamp
        best_ck, items = max(groups.items(), key=lambda kv: (len(kv[1]), max(i['ts'] for i in kv[1])))
        return {'status': 'ok', 'checksum': best_ck, 'nodes': [i['node'] for i in items], 'files': [i['file'] for i in items]}

    def recover(self, dest_db_enc_path: str, preferred_node: Optional[str] = None) -> Dict:
        """Recover the main encrypted DB from a shadow node snapshot."""
        inv = self.inventory()
        if not inv:
            return {'ok': False, 'error': 'no_snapshots'}
        # choose file: preferred node first, else most recent
        cand = None
        if preferred_node:
            cand = max([i for i in inv if i['node'] == preferred_node], key=lambda x: x['ts'], default=None)
        if not cand:
            cand = max(inv, key=lambda x: x['ts'])
        try:
            data = Path(cand['file']).read_bytes()
            Path(dest_db_enc_path).parent.mkdir(parents=True, exist_ok=True)
            Path(dest_db_enc_path).write_bytes(data)
            write_audit_log(self.conn, 'shadow', 'recover', cand['file'], {'dest': dest_db_enc_path})
            return {'ok': True, 'source': cand['file'], 'dest': dest_db_enc_path}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
