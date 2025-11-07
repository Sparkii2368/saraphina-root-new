#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load test: simulate multiple devices pushing GPS updates
"""
import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.geotracker import Geotracker

ke = KnowledgeEngine()
geo = Geotracker(ke)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 50

lat0, lon0 = 37.7749, -122.4194

devs = [f"load-dev-{i:03d}" for i in range(N)]

for s in range(steps):
    for d in devs:
        lat = lat0 + random.uniform(-0.001, 0.001)
        lon = lon0 + random.uniform(-0.001, 0.001)
        geo.ingest_gps(d, lat, lon, accuracy=random.uniform(5, 20))
    time.sleep(0.05)
print(f"Done: {N} devices, {steps} steps")
