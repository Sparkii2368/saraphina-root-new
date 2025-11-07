#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chaos test: randomly inject failures and delays in Geotracker calls
"""
import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.geotracker import Geotracker

ke = KnowledgeEngine()
geo = Geotracker(ke)

device = sys.argv[1] if len(sys.argv) > 1 else 'chaos-device-001'
for i in range(100):
    if random.random() < 0.1:
        time.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.05:
        # simulate faulty input
        try:
            geo.ingest_gps(device, float('nan'), float('nan'), accuracy=9999)
        except Exception:
            pass
    else:
        lat = 37.7749 + random.uniform(-0.0005, 0.0005)
        lon = -122.4194 + random.uniform(-0.0005, 0.0005)
        geo.ingest_gps(device, lat, lon, accuracy=random.uniform(5, 15))
print('Chaos run complete')
