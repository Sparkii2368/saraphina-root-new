#!/usr/bin/env python3
"""
SelfUpgradeOrchestrator - Autonomous self-upgrade system
Saraphina can read roadmap, find gaps, generate code, and upgrade herself
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .roadmap_parser import RoadmapParser
from .capability_auditor import CapabilityAuditor
from .code_forge import CodeForge
from .hot_reload_manager import HotReloadManager

logger = logging.getLogger("SelfUpgrade")


class SelfUpgradeOrchestrator:
    """
    Main orchestrator for autonomous self-upgrades
    
    This implements the complete autonomous upgrade loop:
    1. Parse roadmap from desktop
    2. Audit current capabilities
    3. Find gaps
    4. Generate code to fill gaps using GPT-4
    5. Validate and apply code
    6. Learn from results
    """
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina"):
        self.saraphina_root = Path(saraphina_root)
        self.desktop_path = Path.home() / "Desktop"
        
        # Initialize components
        self.roadmap_parser = RoadmapParser()
        self.auditor = CapabilityAuditor(str(self.saraphina_root))
        
        # CodeForge and HotReloadManager require API key
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.forge = CodeForge(api_key)
            self.hot_reload = HotReloadManager(str(self.saraphina_root))
        else:
            logger.warning("No OpenAI API key - code generation disabled")
            self.forge = None
            self.hot_reload = None
        
        # State
        self.current_roadmap = None
        self.current_gaps = []
        self.upgrade_history: List[Dict[str, Any]] = []
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Run complete audit cycle:
        1. Load roadmap from desktop
        2. Scan current modules
        3. Compare and find gaps
        4. Return structured report
        """
        logger.info("🔍 Starting full capability audit...")
        
        # Load roadmap
        roadmap_path = self.desktop_path / "roadmap.txt"
        if not roadmap_path.exists():
            return {
                "success": False,
                "error": f"roadmap.txt not found at {roadmap_path}"
            }
        
        logger.info(f"📄 Loading roadmap from {roadmap_path}")
        self.current_roadmap = self.roadmap_parser.parse_file(str(roadmap_path))
        
        if not self.current_roadmap.phases:
            return {
                "success": False,
                "error": "Failed to parse roadmap"
            }
        
        logger.info(f"✓ Parsed {len(self.current_roadmap.phases)} phases from roadmap")
        
        # Scan current system
        logger.info("🔍 Scanning current system modules...")
        capabilities = self.auditor.scan_modules()
        logger.info(f"✓ Found {len(capabilities)} existing capabilities")
        
        # Find gaps
        logger.info("📊 Comparing to roadmap requirements...")
        self.current_gaps = self.auditor.audit_against_roadmap(self.current_roadmap)
        
        # Generate report
        report = self.auditor.generate_report()
        report['success'] = True
        report['roadmap_phases'] = len(self.current_roadmap.phases)
        report['roadmap_fixes'] = len(self.current_roadmap.immediate_fixes)
        
        logger.info(f"✅ Audit complete: {len(self.current_gaps)} gaps found")
        
        return report
    
    def auto_upgrade_next_gap(self, ui_callback=None) -> Dict[str, Any]:
        """
        Automatically upgrade the next highest-priority gap
        
        THIS IS THE CORE AUTONOMOUS UPGRADE FUNCTION:
        1. Get next gap
        2. Generate code using GPT-4
        3. Validate it
        4. Apply it live
        5. Learn from result
        """
        
        def log(msg: str):
            logger.info(msg)
            if ui_callback:
                ui_callback(msg)
        
        if not self.current_gaps:
            log("⚠️ No gaps to upgrade. Run audit first.")
            return {"success": False, "error": "No gaps found"}
        
        if not self.forge:
            log("❌ CodeForge not available (missing API key)")
            return {"success": False, "error": "Code generation disabled"}
        
        # Get highest priority gap
        gap = self.current_gaps[0]
        log(f"🎯 Targeting gap: {gap.gap_id} - {gap.requirement[:60]}...")
        log(f"   Severity: {gap.severity.upper()} | Phase: {gap.phase}")
        
        try:
            # STEP 1: Generate code using GPT-4
            log("🔨 Generating code with GPT-4...")
            artifact = self.forge.generate_from_gap(gap)
            log(f"✓ Generated {artifact.estimated_loc} lines of code")
            log(f"   Risk score: {artifact.risk_score:.2f}")
            
            # STEP 2: Basic validation
            if artifact.new_files:
                log(f"📄 New files: {', '.join(artifact.new_files.keys())}")
            if artifact.code_diffs:
                log(f"✏️  Modified files: {', '.join(artifact.code_diffs.keys())}")
            
            # STEP 3: Apply with hot-reload
            log("🚀 Applying code changes...")
            apply_result = self.hot_reload.apply_artifact(artifact)
            
            if apply_result['success']:
                log(f"✅ Successfully applied {artifact.artifact_id}")
                log(f"   Files modified: {apply_result['files_modified']}")
                log(f"   Modules reloaded: {apply_result['modules_reloaded']}")
                
                # Remove gap from list
                self.current_gaps.pop(0)
                
                # Log upgrade
                self.upgrade_history.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'gap_id': gap.gap_id,
                    'requirement': gap.requirement,
                    'artifact_id': artifact.artifact_id,
                    'status': 'success',
                    'files_modified': apply_result['files_modified']
                })
                
                return {
                    "success": True,
                    "gap_id": gap.gap_id,
                    "artifact_id": artifact.artifact_id,
                    "requirement": gap.requirement,
                    "files_modified": apply_result['files_modified'],
                    "modules_reloaded": apply_result['modules_reloaded'],
                    "remaining_gaps": len(self.current_gaps)
                }
            else:
                log(f"❌ Failed to apply: {apply_result.get('error')}")
                log("🔄 Changes rolled back")
                
                return {
                    "success": False,
                    "gap_id": gap.gap_id,
                    "error": apply_result.get('error'),
                    "rolled_back": True
                }
        
        except Exception as e:
            log(f"💥 Upgrade failed: {e}")
            return {
                "success": False,
                "gap_id": gap.gap_id,
                "error": str(e)
            }
    
    def upgrade_loop(self, max_iterations: int = 10, ui_callback=None) -> Dict[str, Any]:
        """
        Run continuous upgrade loop
        
        Autonomously upgrade multiple gaps until:
        - All gaps fixed
        - Max iterations reached
        - Critical error occurs
        """
        
        def log(msg: str):
            logger.info(msg)
            if ui_callback:
                ui_callback(msg)
        
        log("🚀 Starting autonomous upgrade loop...")
        log(f"   Max iterations: {max_iterations}")
        log(f"   Current gaps: {len(self.current_gaps)}")
        
        successful_upgrades = 0
        failed_upgrades = 0
        
        for iteration in range(max_iterations):
            if not self.current_gaps:
                log("✅ All gaps resolved!")
                break
            
            log(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")
            
            result = self.auto_upgrade_next_gap(ui_callback)
            
            if result['success']:
                successful_upgrades += 1
                log(f"✓ Upgrade successful ({successful_upgrades} total)")
            else:
                failed_upgrades += 1
                log(f"✗ Upgrade failed ({failed_upgrades} total)")
                
                # Stop on too many failures
                if failed_upgrades >= 3:
                    log("⚠️ Too many failures, stopping loop")
                    break
        
        summary = {
            "success": True,
            "iterations_run": iteration + 1,
            "successful_upgrades": successful_upgrades,
            "failed_upgrades": failed_upgrades,
            "remaining_gaps": len(self.current_gaps),
            "upgrade_history": self.upgrade_history[-10:]  # Last 10
        }
        
        log(f"\n🏁 Upgrade loop complete:")
        log(f"   Successful: {successful_upgrades}")
        log(f"   Failed: {failed_upgrades}")
        log(f"   Remaining gaps: {len(self.current_gaps)}")
        
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """Get current upgrade system status"""
        return {
            "roadmap_loaded": self.current_roadmap is not None,
            "phases_parsed": len(self.current_roadmap.phases) if self.current_roadmap else 0,
            "current_gaps": len(self.current_gaps),
            "capabilities_count": len(self.auditor.capabilities),
            "forge_available": self.forge is not None,
            "upgrade_history_count": len(self.upgrade_history),
            "last_upgrade": self.upgrade_history[-1] if self.upgrade_history else None
        }
    
    def list_gaps(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all current gaps, optionally filtered by severity"""
        gaps = self.current_gaps
        
        if severity:
            gaps = [g for g in gaps if g.severity == severity.lower()]
        
        return [
            {
                'gap_id': g.gap_id,
                'requirement': g.requirement,
                'severity': g.severity,
                'phase': g.phase,
                'current_status': g.current_status,
                'estimated_effort': g.estimated_effort
            }
            for g in gaps
        ]
    
    def get_next_gap(self) -> Optional[Dict[str, Any]]:
        """Get the next gap that will be upgraded"""
        if not self.current_gaps:
            return None
        
        gap = self.current_gaps[0]
        return {
            'gap_id': gap.gap_id,
            'requirement': gap.requirement,
            'severity': gap.severity,
            'phase': gap.phase,
            'estimated_effort': gap.estimated_effort
        }
