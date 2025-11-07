#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Saraphina Enhanced CLI with AI Integration
Commands:
  /track <device> [--interval SEC] [--duration SEC] [--from-lat LAT --from-lon LON] [--simulate]
  /locate <device> [--from-lat LAT --from-lon LON] [--wifi-json JSON] [--ble-json JSON]
  /lost workflow start <device> [--simulate]
  /ai - Natural conversation with Saraphina AI
  /status - Show AI learning status
  /help - Show all commands

Provides:
- Confidence radius output and map links
- Text guidance (bearing/heading). Optional RSSI-based hints via provided scans
- Auto-stop tracking after timeout for privacy
- Interactive AI assistant with learning capabilities
"""

import sys
import time
import json
import math
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure src on path
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from saraphina.knowledge_engine import KnowledgeEngine
from saraphina.geotracker import Geotracker
from saraphina.recovery_orchestrator import RecoveryOrchestrator
from saraphina.nlp_router import parse_intent
from saraphina.ai_core import SaraphinaAI

LOG = logging.getLogger("saraphina.cli")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --------------------------- Helpers ---------------------------

def bearing_to_compass(bearing: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((bearing / 22.5) + 0.5) % 16
    return dirs[idx]


def gmaps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}"


def osm_link(lat: float, lon: float, zoom: int = 17) -> str:
    return f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map={zoom}/{lat:.6f}/{lon:.6f}"


def gmaps_directions_link(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={from_lat:.6f},{from_lon:.6f}"
        f"&destination={to_lat:.6f},{to_lon:.6f}"
        "&travelmode=walking"
    )


def compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Simple wrapper to avoid importing bearing from Geotracker statically
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    return brng


def parse_float(val: Optional[str]) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except Exception:
        return None


def load_scans_json(json_str: Optional[str]) -> List[Dict[str, Any]]:
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception as e:
        LOG.warning(f"Invalid JSON for scans: {e}")
        return []


# --------------------------- Core Commands ---------------------------

def cmd_locate(device_id: str, from_lat: Optional[float], from_lon: Optional[float],
               wifi_json: Optional[str], ble_json: Optional[str], simulate: bool = False) -> int:
    ke = KnowledgeEngine()
    geo = Geotracker(ke)

    if simulate:
        # Seed some known infrastructure and a last-known GPS
        geo.register_wifi_ap("00:11:22:33:44:55", "Home_WiFi", 37.7749, -122.4194, accuracy=30.0)
        geo.register_wifi_ap("AA:BB:CC:DD:EE:FF", "Office_WiFi", 37.7750, -122.4190, accuracy=25.0)
        geo.register_ble_beacon("beacon-001", 37.7749, -122.4194, accuracy=50.0)
        geo.ingest_gps(device_id, 37.7749, -122.4194, altitude=15.0, accuracy=9.0,
                       metadata={"simulated": True})

    # Optional triangulation updates if scans provided
    wifi_scans = load_scans_json(wifi_json)
    if wifi_scans:
        geo.ingest_wifi(device_id, wifi_scans, metadata={"manual_scans": True})

    ble_scans = load_scans_json(ble_json)
    if ble_scans:
        geo.ingest_ble(device_id, ble_scans, metadata={"manual_scans": True})

    conf = geo.calculate_confidence_radius(device_id)
    if not conf.get("has_location"):
        LOG.info("No location available for device.")
        return 2

    lat = conf["center"]["lat"]
    lon = conf["center"]["lon"]
    radius = conf["radius_meters"] or conf.get("base_accuracy", 100.0)
    age_sec = conf.get("age_seconds", None)

    LOG.info(f"Device: {device_id}")
    LOG.info(f"Last source: {conf.get('last_source')}  |  Confidence: {conf.get('confidence')}  |  Age: {age_sec:.1f}s")
    LOG.info(f"Center: ({lat:.6f}, {lon:.6f})  ±{radius:.1f} m")
    LOG.info(f"Map: {gmaps_link(lat, lon)}")
    LOG.info(f"OSM:  {osm_link(lat, lon)}")

    if from_lat is not None and from_lon is not None:
        brng = compute_bearing(from_lat, from_lon, lat, lon)
        direction = bearing_to_compass(brng)
        LOG.info(f"Guidance: Head {direction} toward target (bearing {brng:.1f}°)")
        LOG.info(f"Directions: {gmaps_directions_link(from_lat, from_lon, lat, lon)}")
    else:
        LOG.info("Guidance: Provide --from-lat and --from-lon for directional hints")

    # RSSI-based contextual hint (if scans provided)
    if wifi_scans:
        strongest = max(wifi_scans, key=lambda x: x.get('rssi', -99))
        bssid = strongest.get('bssid', 'unknown')
        rssi = strongest.get('rssi', -99)
        LOG.info(f"Hint: Move toward stronger signal of Wi‑Fi BSSID {bssid} (RSSI {rssi} dBm)")
    if ble_scans:
        strongest_b = max(ble_scans, key=lambda x: x.get('rssi', -99))
        bid = strongest_b.get('id') or strongest_b.get('uuid', 'unknown')
        rssi_b = strongest_b.get('rssi', -99)
        LOG.info(f"Hint: BLE beacon {bid} strongest at {rssi_b} dBm—you're getting closer")

    return 0


def cmd_track(device_id: str, interval: float, duration: Optional[float],
              from_lat: Optional[float], from_lon: Optional[float], simulate: bool = False) -> int:
    ke = KnowledgeEngine()
    geo = Geotracker(ke)

    if simulate:
        # Seed environment and an initial point
        geo.register_ble_beacon("beacon-001", 37.7749, -122.4194, accuracy=50.0)
        geo.register_ble_beacon("beacon-002", 37.7751, -122.4192, accuracy=50.0)
        geo.ingest_gps(device_id, 37.7749, -122.4194, accuracy=9.0, metadata={"simulated": True})

    max_duration = duration if duration is not None else min(600.0, getattr(geo, 'tracking_timeout', 3600))
    LOG.info(f"Tracking {device_id} every {interval:.1f}s for up to {max_duration:.0f}s (auto-stop for privacy)")

    t0 = time.time()
    updates = 0
    last_lat = last_lon = None

    try:
        while True:
            conf = geo.calculate_confidence_radius(device_id)
            if conf.get("has_location"):
                lat = conf["center"]["lat"]
                lon = conf["center"]["lon"]
                radius = conf["radius_meters"]
                src = conf.get("last_source")
                LOG.info(f"{src} -> ({lat:.6f}, {lon:.6f}) ±{radius:.1f}m | {conf.get('confidence')} | age {conf.get('age_seconds'):.1f}s")

                if from_lat is not None and from_lon is not None:
                    brng = compute_bearing(from_lat, from_lon, lat, lon)
                    LOG.info(f"Guidance: {bearing_to_compass(brng)} ({brng:.1f}°)")

                last_lat, last_lon = lat, lon
                updates += 1
            else:
                LOG.info("No location yet. Waiting…")

            if time.time() - t0 >= max_duration:
                LOG.info("Auto-stopping tracking to protect privacy")
                break

            time.sleep(max(0.1, interval))
    except KeyboardInterrupt:
        LOG.info("Tracking stopped by user")

    LOG.info(f"Track session complete. Updates: {updates}")
    if last_lat is not None:
        LOG.info(f"Last map: {gmaps_link(last_lat, last_lon)}")
    return 0


def cmd_lost_workflow_start(device_id: str, simulate: bool = False) -> int:
    ke = KnowledgeEngine()
    geo = Geotracker(ke)
    rec = RecoveryOrchestrator(ke, geo)

    if simulate:
        # Seed last-known location for better guidance
        geo.ingest_gps(device_id, 37.7749, -122.4194, accuracy=12.0, metadata={"simulated": True})

    session = rec.initiate_recovery(device_id, reason="User reported device missing", priority=7)
    LOG.info(f"Recovery session started: {session.session_id}")

    if not simulate:
        # Print first step and exit; user will run commands and call API to proceed
        step = session.get_current_step()
        LOG.info(f"Step 1: {step.title}")
        if step.command:
            LOG.info(f"Run: {step.command}")
        LOG.info("Provide step result via API/UI to proceed.")
        return 0

    # Auto-simulate typical flow: location success, ping fail, scan fail, BLE success -> resolved
    flow = [
        ("Location data retrieved within confidence radius", True),
        ("Ping timeout", False),
        ("No matching devices on network", False),
        ("Device detected via Bluetooth RSSI -60", True)
    ]

    for msg, _ in flow:
        res = rec.execute_step(session.session_id, step_result=msg, feedback=msg)
        LOG.info(f"Step -> {res['status']}")
        if res['status'] == 'resolved':
            LOG.info("Device recovered! 🎉")
            break

    stats = rec.get_recovery_statistics()
    LOG.info(f"Sessions: {stats['total_sessions']}  Resolved: {stats['resolved_sessions']}  Failed: {stats['failed_sessions']}")
    return 0


# --------------------------- AI & Interactive Commands ---------------------------

def cmd_help() -> int:
    """Display comprehensive help"""
    print("""
🌟 SARAPHINA - Advanced AI Device Tracking System
================================================

DEVICE TRACKING COMMANDS:
  /locate <device> [options]    - Locate a device
    Options: --from-lat LAT --from-lon LON --wifi-json JSON --ble-json JSON --simulate
  
  /track <device> [options]     - Track device in real-time
    Options: --interval SEC --duration SEC --from-lat LAT --from-lon LON --simulate
  
  /lost workflow start <device> - Start lost device recovery workflow
    Options: --simulate

AI ASSISTANT COMMANDS:
  /ai                           - Start interactive AI conversation mode
  /status                       - Show AI learning status and system info
  /help                         - Show this help message
  /exit or /quit                - Exit the application

INTERACTIVE MODE:
  Run without arguments to enter interactive mode where you can:
  - Chat naturally with Saraphina AI
  - Run any command by typing it
  - Ask questions about device tracking
  - Get intelligent assistance

EXAMPLES:
  python saraphina_cli.py /locate phone-001 --simulate
  python saraphina_cli.py /track tablet-001 --interval 5 --simulate
  python saraphina_cli.py /ai
  python saraphina_cli.py  (starts interactive mode)

""")
    return 0

def cmd_ai_status() -> int:
    """Show AI learning status"""
    ai = SaraphinaAI()
    print("\n" + ai.get_status_summary())
    print("\n💡 The AI learns and grows with each interaction!\n")
    return 0

def interactive_mode() -> int:
    """Run interactive terminal with AI"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║   🌟 SARAPHINA INTERACTIVE TERMINAL 🌟                      ║
║   Advanced AI Device Tracking System                         ║
╚══════════════════════════════════════════════════════════════╝

Welcome! I'm Saraphina, your AI assistant.
Type /help for commands, or just chat with me naturally.
Type /exit or /quit to leave.
""")
    
    ai = SaraphinaAI()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print("\n👋 Goodbye! Thanks for using Saraphina.")
                print(ai.get_status_summary())
                break
            
            # Check for help command
            if user_input.lower() in ['/help', 'help']:
                cmd_help()
                continue
            
            # Check for status command
            if user_input.lower() in ['/status', 'status']:
                print("\n" + ai.get_status_summary())
                continue
            
            # Check for device commands
            if user_input.startswith('/'):
                # Parse and execute command
                result = execute_command(user_input)
                if result is not None:
                    continue
            
            # Otherwise, process as natural language with AI
            response = ai.process_query(user_input)
            print(f"\n🤖 Saraphina: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using Saraphina.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            LOG.error(f"Interactive mode error: {e}", exc_info=True)
    
    return 0

def execute_command(cmd_line: str) -> Optional[int]:
    """Execute a slash command in interactive mode"""
    tokens = cmd_line.split()
    if not tokens:
        return None
    
    cmd = tokens[0].lstrip('/')
    
    # Locate command
    if cmd == 'locate' and len(tokens) >= 2:
        device = tokens[1]
        from_lat = parse_float(tokens[tokens.index('--from-lat') + 1]) if '--from-lat' in tokens else None
        from_lon = parse_float(tokens[tokens.index('--from-lon') + 1]) if '--from-lon' in tokens else None
        wifi_json = tokens[tokens.index('--wifi-json') + 1] if '--wifi-json' in tokens else None
        ble_json = tokens[tokens.index('--ble-json') + 1] if '--ble-json' in tokens else None
        simulate = ('--simulate' in tokens)
        cmd_locate(device, from_lat, from_lon, wifi_json, ble_json, simulate)
        return 0
    
    # Track command
    elif cmd == 'track' and len(tokens) >= 2:
        device = tokens[1]
        interval = parse_float(tokens[tokens.index('--interval') + 1]) if '--interval' in tokens else 10.0
        duration = parse_float(tokens[tokens.index('--duration') + 1]) if '--duration' in tokens else None
        from_lat = parse_float(tokens[tokens.index('--from-lat') + 1]) if '--from-lat' in tokens else None
        from_lon = parse_float(tokens[tokens.index('--from-lon') + 1]) if '--from-lon' in tokens else None
        simulate = ('--simulate' in tokens)
        cmd_track(device, interval or 10.0, duration, from_lat, from_lon, simulate)
        return 0
    
    # Lost workflow command
    elif cmd == 'lost' and len(tokens) >= 4 and tokens[1] == 'workflow' and tokens[2] == 'start':
        device = tokens[3]
        simulate = ('--simulate' in tokens)
        cmd_lost_workflow_start(device, simulate)
        return 0
    
    # AI command
    elif cmd == 'ai':
        print("\n💡 You're already in interactive AI mode! Just type naturally.")
        return 0
    
    else:
        print(f"\n❌ Unknown command: {cmd}. Type /help for available commands.")
        return 1

# --------------------------- Entry ---------------------------

def usage() -> int:
    return cmd_help()


def main(argv: List[str]) -> int:
    # No arguments = interactive mode
    if len(argv) < 2:
        return interactive_mode()

    # Normalize command tokens (support with or without leading '/')
    tokens = [t for t in argv[1:] if t]
    if not tokens:
        return interactive_mode()

    cmd = tokens[0].lstrip('/')

    # /help
    if cmd in ['help', 'h', '?']:
        return cmd_help()
    
    # /status
    if cmd == 'status':
        return cmd_ai_status()
    
    # /ai - Interactive AI mode
    if cmd == 'ai':
        return interactive_mode()

    # /locate
    if cmd == 'locate' and len(tokens) >= 2:
        device = tokens[1]
        # Parse optional flags
        from_lat = parse_float(tokens[tokens.index('--from-lat') + 1]) if '--from-lat' in tokens else None
        from_lon = parse_float(tokens[tokens.index('--from-lon') + 1]) if '--from-lon' in tokens else None
        wifi_json = tokens[tokens.index('--wifi-json') + 1] if '--wifi-json' in tokens else None
        ble_json = tokens[tokens.index('--ble-json') + 1] if '--ble-json' in tokens else None
        simulate = ('--simulate' in tokens)
        return cmd_locate(device, from_lat, from_lon, wifi_json, ble_json, simulate)

    # /track
    if cmd == 'track' and len(tokens) >= 2:
        device = tokens[1]
        interval = parse_float(tokens[tokens.index('--interval') + 1]) if '--interval' in tokens else 10.0
        duration = parse_float(tokens[tokens.index('--duration') + 1]) if '--duration' in tokens else None
        from_lat = parse_float(tokens[tokens.index('--from-lat') + 1]) if '--from-lat' in tokens else None
        from_lon = parse_float(tokens[tokens.index('--from-lon') + 1]) if '--from-lon' in tokens else None
        simulate = ('--simulate' in tokens)
        return cmd_track(device, interval or 10.0, duration, from_lat, from_lon, simulate)

    # /lost workflow start
    if cmd == 'lost' and len(tokens) >= 4 and tokens[1] == 'workflow' and tokens[2] == 'start':
        device = tokens[3]
        simulate = ('--simulate' in tokens)
        return cmd_lost_workflow_start(device, simulate)

    # NLP fallback: treat remaining tokens as a phrase
    phrase = " ".join(tokens)
    intent = parse_intent(phrase)
    if intent:
        if intent["intent"] == "locate":
            return cmd_locate(
                intent["device_id"], intent.get("from_lat"), intent.get("from_lon"), None, None, intent.get("simulate", False)
            )
        if intent["intent"] == "track":
            return cmd_track(
                intent["device_id"], float(intent.get("interval", 10.0)), intent.get("duration"),
                intent.get("from_lat"), intent.get("from_lon"), intent.get("simulate", False)
            )
        if intent["intent"] == "lost_workflow_start":
            return cmd_lost_workflow_start(intent["device_id"], intent.get("simulate", False))
    
    # Unknown command
    print(f"\n❌ Unknown command: {cmd}")
    return usage()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
