#!/usr/bin/env python3
"""
Self-Healing Manager - Orchestrates autonomous error detection and healing
Phase 29: Makes Saraphina resilient and self-repairing
"""

import logging
import threading
import time
from typing import Dict, Optional
from pathlib import Path

from saraphina.error_sentinel import get_error_bus
from saraphina.error_knowledge_base import ErrorKnowledgeBase
from saraphina.research_fix_engine import ResearchFixEngine

logger = logging.getLogger("SelfHealing")


class SelfHealingManager:
    """Manages autonomous error detection and healing"""
    
    def __init__(self):
        # Initialize components
        self.error_kb = ErrorKnowledgeBase()
        self.research_engine = ResearchFixEngine(self.error_kb)
        self.healing_active = True
        self.pending_approvals = []
        
        # Subscribe to error bus
        get_error_bus().subscribe(self._on_error)
        
        # Start healing thread
        self.healing_thread = threading.Thread(target=self._healing_loop, daemon=True)
        self.healing_thread.start()
        
        logger.info("🏥 Self-Healing Manager initialized")
    
    def _on_error(self, error_event: Dict):
        """Handle error event from error bus"""
        
        # Record error
        self.error_kb.record_error(error_event)
        
        # Check if we have a fix
        existing_fix = self.error_kb.get_fix(error_event['error_id'])
        
        if existing_fix:
            logger.info(f"✓ Known error {error_event['error_id']} - fix available")
            return
        
        # New error - needs research
        logger.warning(f"⚠️ New error detected: {error_event['error_id']} in {error_event['subsystem']}")
        
        # If requires approval, add to queue
        if error_event.get('require_approval'):
            self.pending_approvals.append(error_event)
            logger.info(f"Error requires owner approval - queued")
        else:
            # Can auto-research
            self._research_and_fix(error_event)
    
    def _research_and_fix(self, error_event: Dict):
        """Research error and propose fix"""
        
        try:
            logger.info(f"🔬 Researching error {error_event['error_id']}...")
            
            # Use GPT-4 to research
            fix_proposal = self.research_engine.research_error(error_event)
            
            if not fix_proposal:
                logger.warning(f"Could not generate fix for {error_event['error_id']}")
                return
            
            logger.info(f"💡 Fix proposed: {fix_proposal.get('fix_description', '')[:100]}...")
            
            # Test in sandbox
            if self.research_engine.test_fix_in_sandbox(fix_proposal, error_event):
                # Store the fix
                self.research_engine.apply_fix(error_event['error_id'], fix_proposal)
                logger.info(f"✅ Fix stored for {error_event['error_id']}")
                
                # Record success
                self.error_kb.record_heal_success(error_event['error_id'])
            else:
                logger.warning(f"Fix failed sandbox test for {error_event['error_id']}")
                self.error_kb.record_heal_failure(error_event['error_id'])
        
        except Exception as e:
            logger.error(f"Research failed: {e}")
    
    def _healing_loop(self):
        """Background healing loop - processes unfixed errors"""
        
        while self.healing_active:
            try:
                time.sleep(300)  # Every 5 minutes
                
                # Get unfixed errors
                unfixed = self.error_kb.get_unfixed_errors(limit=5)
                
                if unfixed:
                    logger.info(f"🏥 Healing loop: {len(unfixed)} unfixed errors")
                    
                    for error in unfixed:
                        # Only auto-heal if not requires approval
                        if not error['require_approval']:
                            self._research_and_fix(error)
                
            except Exception as e:
                logger.error(f"Healing loop error: {e}")
    
    def get_statistics(self) -> Dict:
        """Get self-healing statistics"""
        return self.error_kb.get_statistics()
    
    def get_pending_approvals(self) -> list:
        """Get errors awaiting owner approval"""
        return self.pending_approvals
    
    def approve_fix(self, error_id: str):
        """Owner approves a fix"""
        # Find in pending
        error = next((e for e in self.pending_approvals if e['error_id'] == error_id), None)
        
        if error:
            self.pending_approvals.remove(error)
            self._research_and_fix(error)
            logger.info(f"✓ Owner approved fix for {error_id}")
    
    def shutdown(self):
        """Shutdown healing manager"""
        self.healing_active = False
        logger.info("Self-Healing Manager shutdown")
