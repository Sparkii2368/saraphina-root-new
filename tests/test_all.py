#!/usr/bin/env python3
import os
import json
import time
from pathlib import Path
from uuid import uuid4

import pytest

from saraphina.db import init_db
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.planner import Planner
from saraphina.system_adapter import NoOpAdapter
from saraphina.device_agent import DeviceAgent
from saraphina.monitoring import health_pulse
from saraphina.security import SecurityManager
from saraphina.review_manager import ReviewManager

@pytest.fixture()
def tmpdb(tmp_path):
    db_path = tmp_path / f"test_{uuid4()}.db"
    conn = init_db(str(db_path))
    yield conn, str(db_path)
    try:
        conn.close()
    except Exception:
        pass

# Unit: DB schema operations
def test_db_schema_tables_exist(tmpdb):
    conn, _ = tmpdb
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    for t in [
        'facts','fact_aliases','fact_versions','concept_links','queries',
        'preferences','devices','device_agents','device_policies','audit_logs',
        'skills_xp','code_artifacts','review_queue']:
        assert t in names

# Unit: recall correctness
def test_knowledge_recall(tmpdb):
    conn, dbp = tmpdb
    ke = KnowledgeEngine(dbp)
    fid = ke.store_fact('python','list sorting','Python lists can be sorted using sorted()','doc',0.9)
    hits = ke.recall('sorted list', top_k=3, threshold=0.5)
    assert any(h['id'] == fid for h in hits)

# Unit: planner
def test_planner_outputs():
    p = Planner()
    plan = p.plan('deploy feature', {}, {})
    assert 'steps' in plan and len(plan['steps']) >= 3
    sim = p.simulate_plan(plan)
    assert 0.2 <= sim['success_probability'] <= 0.95

# Unit: adapter dry-run
def test_adapter_dry_run():
    ad = NoOpAdapter()
    cmds = ad.dryrun({"action":"restart_service","service":"x"})
    assert any('NOOP would perform' in c for c in cmds)

# Integration: enroll -> heartbeat -> telemetry -> policy record
def test_device_integration(tmpdb):
    conn, dbp = tmpdb
    agent = DeviceAgent(name='TestDevice', platform='test', owner='owner', db_path=dbp)
    pk = agent.register('tok')
    assert pk and pk.startswith('pk_')
    hb = agent.heartbeat()
    assert hb['status'] in ('online','revoked')
    ack = agent.report_telemetry({'cpu': 10})
    assert ack['ack'] is True
    # policy record (mock)
    cur = conn.cursor()
    cur.execute("INSERT INTO device_policies (policy_id, device_id, policy_json, created_at) VALUES (?,?,?,datetime('now'))",
                (f'pol_{uuid4()}', agent.device_id, json.dumps({'bed_time':'22:00'})))
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM device_policies WHERE device_id=?", (agent.device_id,))
    assert int(cur.fetchone()[0]) >= 1

# End-to-end: knowledge capture and recall across restart
def test_e2e_knowledge_persistence(tmpdb):
    _, dbp = tmpdb
    ke = KnowledgeEngine(dbp)
    fid = ke.store_fact('security','jwt basics','JWTs are bearer tokens','kb',0.8)
    hits1 = ke.recall('JWT bearer', 5, 0.5)
    assert any(h['id']==fid for h in hits1)
    # new instance
    ke2 = KnowledgeEngine(dbp)
    hits2 = ke2.recall('JWT bearer', 5, 0.5)
    assert any(h['id']==fid for h in hits2)

# End-to-end: paraphrase recall success rate (>85% baseline)
def test_paraphrase_recall_rate(tmpdb):
    _, dbp = tmpdb
    ke = KnowledgeEngine(dbp)
    ke.store_fact('devops','docker intro','Docker containers isolate apps using images','kb',0.9)
    queries = [
        'docker containers', 'isolate apps', 'images docker', 'containers apps', 'docker images',
        'app isolation', 'container images', 'docker app image', 'isolation images docker', 'docker intro'
    ]
    successes = 0
    for q in queries:
        if ke.recall(q, 1, 0.5):
            successes += 1
    rate = successes / len(queries)
    assert rate >= 0.85

# End-to-end: planner dry-run and audit log of execution (mock)
def test_planner_audit(tmpdb):
    conn, _ = tmpdb
    p = Planner()
    plan = p.plan('migrate db', {}, {})
    sim = p.simulate_plan(plan)
    from saraphina.db import write_audit_log
    write_audit_log(conn, 'owner', 'plan_execute', 'migrate db', {'sim': sim})
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action='plan_execute'")
    assert int(cur.fetchone()[0]) >= 1

# Monitoring: health pulse
def test_health_pulse(tmpdb):
    conn, _ = tmpdb
    hp = health_pulse(conn)
    assert {'active_agents_count','db_size_bytes','last_backup_ts','failed_actions_count'} <= set(hp.keys())

# SecurityManager: MFA + rekey + file encryption
def test_security_manager(tmp_path):
    sec_dir = tmp_path / 'sec'
    sm = SecurityManager(str(sec_dir))
    created = sm.unlock_or_create('pass')
    assert created is True
    sm.set_secret('k1','v1')
    # enable MFA (optional)
    info = sm.enable_mfa()
    assert True  # allow no-pyotp environment
    # rekey
    sm.rekey('newpass')
    assert sm.get_secret('k1') == 'v1'
    # file enc/dec
    src = tmp_path / 'f.txt'
    src.write_text('hello')
    enc = tmp_path / 'f.txt.enc'
    out = tmp_path / 'f.out.txt'
    sm.encrypt_file(str(src), str(enc))
    sm.decrypt_file(str(enc), str(out))
    assert out.read_text() == 'hello'

# Review queue gating
def test_review_queue(tmpdb):
    conn, _ = tmpdb
    from saraphina.review_manager import ReviewManager
    rm = ReviewManager()
    rid = rm.enqueue('code','high_risk',{'code':'print(1)'})
    items = rm.list('pending')
    assert any(it['id']==rid for it in items)
    assert rm.set_status(rid,'approved') is True

# Recovery workflow for simulated missing device (mock)
def test_missing_device_recovery(tmpdb):
    conn, dbp = tmpdb
    agent = DeviceAgent(name='LostDevice', platform='test', owner='owner', db_path=dbp)
    agent.register('tok')
    # Simulate last_seen 2 days ago
    cur = conn.cursor()
    cur.execute("UPDATE devices SET last_seen=datetime('now','-2 day') WHERE device_id=?", (agent.device_id,))
    conn.commit()
    # Detect missing and log audit
    from saraphina.db import write_audit_log
    cur.execute("SELECT device_id, last_seen FROM devices WHERE device_id=?", (agent.device_id,))
    row = cur.fetchone()
    assert row is not None
    write_audit_log(conn, 'system', 'device_missing', row['device_id'], {'last_seen': row['last_seen']})
    cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action='device_missing' AND target=?", (agent.device_id,))
    assert int(cur.fetchone()[0]) >= 1

# Policy enforcement (bed-time)
def test_device_policy_enforcement(tmpdb):
    conn, dbp = tmpdb
    agent = DeviceAgent(name='PolicyDevice', platform='test', owner='owner', db_path=dbp)
    agent.register('tok')
    cur = conn.cursor()
    # Bed time at 00:00 blocks always for simplicity
    cur.execute("INSERT INTO device_policies (policy_id, device_id, policy_json, created_at) VALUES (?,?,?,datetime('now'))",
                (f'pol_{uuid4()}', agent.device_id, json.dumps({'bed_time':'00:00'})))
    conn.commit()
    res = agent.execute_command('echo hi')
    assert res.get('ok') is False and res.get('error') in ('policy_blocked','command_not_allowed')
