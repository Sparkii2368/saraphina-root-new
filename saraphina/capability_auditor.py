#!/usr/bin/env python3
"""
CapabilityAuditor - Audits current system capabilities and compares to roadmap
"""
import os
import re
import ast
import inspect
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("CapabilityAuditor")


@dataclass
class Capability:
    """Represents a system capability"""
    name: str
    module: str
    status: str  # 'active', 'partial', 'missing', 'broken'
    version: str = "1.0.0"
    health_score: float = 1.0
    methods: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Gap:
    """Represents a gap between current state and roadmap"""
    gap_id: str
    requirement: str
    current_status: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    phase: str
    deliverable: str
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = ""  # '1-2 days', '1 week', etc


class CapabilityAuditor:
    """Audit Saraphina's current capabilities against roadmap"""
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina"):
        self.saraphina_root = Path(saraphina_root)
        self.capabilities: Dict[str, Capability] = {}
        self.gaps: List[Gap] = []
    
    def scan_modules(self) -> Dict[str, Capability]:
        """Scan all Python modules and extract capabilities"""
        logger.info("Scanning Saraphina modules...")
        
        py_files = list(self.saraphina_root.glob("*.py"))
        
        for py_file in py_files:
            if py_file.name.startswith('_'):
                continue
            
            try:
                cap = self._analyze_module(py_file)
                if cap:
                    self.capabilities[cap.name] = cap
            except Exception as e:
                logger.debug(f"Failed to analyze {py_file.name}: {e}")
        
        logger.info(f"Found {len(self.capabilities)} capabilities")
        return self.capabilities
    
    def _analyze_module(self, file_path: Path) -> Optional[Capability]:
        """Analyze a Python module file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Find main class
            main_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Skip test/mock/base classes
                    if not any(x in node.name.lower() for x in ['test', 'mock', 'base']):
                        main_class = node
                        break
            
            if not main_class:
                return None
            
            # Extract methods
            methods = []
            for item in main_class.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                    methods.append(item.name)
            
            # Extract dependencies from imports
            dependencies = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'saraphina' in node.module:
                        dependencies.append(node.module.split('.')[-1])
            
            # Check if module is working
            status = 'active'
            health_score = 1.0
            
            # Look for error handling, TODO markers
            if 'TODO' in content or 'FIXME' in content:
                status = 'partial'
                health_score = 0.7
            
            if 'raise NotImplementedError' in content:
                status = 'partial'
                health_score = 0.5
            
            return Capability(
                name=main_class.name,
                module=file_path.stem,
                status=status,
                health_score=health_score,
                methods=methods,
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.debug(f"Module analysis error for {file_path}: {e}")
            return None
    
    def audit_against_roadmap(self, roadmap) -> List[Gap]:
        """Compare current capabilities against roadmap requirements"""
        logger.info("Auditing capabilities against roadmap...")
        
        self.gaps = []
        gap_counter = 1
        
        # Check each phase
        for phase in roadmap.phases:
            for deliverable in phase.deliverables:
                gap = self._check_deliverable(
                    phase, deliverable, gap_counter
                )
                if gap:
                    self.gaps.append(gap)
                    gap_counter += 1
        
        # Check immediate fixes
        for fix in roadmap.immediate_fixes:
            gap = self._check_fix(fix, gap_counter)
            if gap:
                self.gaps.append(gap)
                gap_counter += 1
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.gaps.sort(key=lambda g: severity_order.get(g.severity, 99))
        
        logger.info(f"Found {len(self.gaps)} gaps")
        return self.gaps
    
    def _check_deliverable(self, phase, deliverable: str, gap_id: int) -> Optional[Gap]:
        """Check if a deliverable is implemented"""
        
        # Extract key terms from deliverable
        deliverable_lower = deliverable.lower()
        
        # Map deliverables to expected modules/capabilities
        capability_checks = {
            'capability model': 'CapabilityAuditor',
            'roadmap parser': 'RoadmapParser',
            'gap diff engine': 'CapabilityAuditor',
            'spec generator': 'SpecGenerator',
            'spec schema': 'SpecGenerator',
            'acceptance test': 'AcceptanceTest',
            'code forge': 'CodeForge',
            'generator': 'CodeForge',
            'static analysis': 'StaticAnalyzer',
            'sandbox': 'SandboxValidator',
            'hot-reload': 'HotReloadManager',
            'hot reload': 'HotReloadManager',
            'risk scoring': 'RiskModel',
            'policy tier': 'PolicyEngine',
            'approval': 'ApprovalGate',
            'audit trail': 'AuditLog',
            'error sentinel': 'ErrorSentinel',
            'error kb': 'ErrorKnowledgeBase',
            'self-heal': 'SelfHealingManager',
            'scheduler': 'UpgradeScheduler'
        }
        
        # Check if any expected capability exists
        expected_cap = None
        for keyword, cap_name in capability_checks.items():
            if keyword in deliverable_lower:
                expected_cap = cap_name
                break
        
        if not expected_cap:
            return None  # Can't map to specific capability
        
        # Check if capability exists
        if expected_cap not in self.capabilities:
            # Determine severity based on phase
            severity_map = {
                'A': 'critical',
                'B': 'critical', 
                'C': 'high',
                'D': 'high',
                'E': 'medium',
                'F': 'medium',
                'G': 'low'
            }
            
            return Gap(
                gap_id=f"GAP-{gap_id:03d}",
                requirement=deliverable,
                current_status='missing',
                severity=severity_map.get(phase.id, 'medium'),
                phase=f"Phase {phase.id}",
                deliverable=deliverable,
                estimated_effort=self._estimate_effort(deliverable)
            )
        
        # Check if capability is healthy
        cap = self.capabilities[expected_cap]
        if cap.health_score < 0.8:
            return Gap(
                gap_id=f"GAP-{gap_id:03d}",
                requirement=deliverable,
                current_status=f"partial ({cap.health_score:.0%})",
                severity='medium',
                phase=f"Phase {phase.id}",
                deliverable=deliverable,
                estimated_effort="1-2 days"
            )
        
        return None
    
    def _check_fix(self, fix: Dict[str, str], gap_id: int) -> Optional[Gap]:
        """Check if an immediate fix is implemented"""
        
        issue_lower = fix['issue'].lower()
        
        # Check for specific fixes
        if 'hash' in issue_lower or 'robotic tone' in issue_lower:
            # Check if response formatter handles this
            if 'ResponseFormatter' not in self.capabilities:
                return Gap(
                    gap_id=f"FIX-{gap_id:03d}",
                    requirement=fix['issue'],
                    current_status='missing',
                    severity='high',
                    phase='Immediate Fixes',
                    deliverable=fix['fix'],
                    estimated_effort='1-2 hours'
                )
        
        elif 'last update' in issue_lower:
            # Check for SystemMetadata
            if 'SystemMetadata' not in self.capabilities:
                return Gap(
                    gap_id=f"FIX-{gap_id:03d}",
                    requirement=fix['issue'],
                    current_status='missing',
                    severity='medium',
                    phase='Immediate Fixes',
                    deliverable=fix['fix'],
                    estimated_effort='2-3 hours'
                )
        
        elif 'deep learning' in issue_lower or 'fast front' in issue_lower:
            # Check for BackgroundLearner
            if 'BackgroundLearner' not in self.capabilities:
                return Gap(
                    gap_id=f"FIX-{gap_id:03d}",
                    requirement=fix['issue'],
                    current_status='missing',
                    severity='high',
                    phase='Immediate Fixes',
                    deliverable=fix['fix'],
                    estimated_effort='1 day'
                )
        
        return None
    
    def _estimate_effort(self, deliverable: str) -> str:
        """Estimate implementation effort"""
        deliverable_lower = deliverable.lower()
        
        # Simple heuristics
        if any(word in deliverable_lower for word in ['parser', 'validator', 'formatter']):
            return '1-2 days'
        elif any(word in deliverable_lower for word in ['engine', 'manager', 'orchestrator']):
            return '3-5 days'
        elif any(word in deliverable_lower for word in ['sandbox', 'hot-reload', 'self-heal']):
            return '1 week'
        else:
            return '2-3 days'
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate structured audit report"""
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for gap in self.gaps:
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1
        
        # Group by phase
        phase_gaps = {}
        for gap in self.gaps:
            if gap.phase not in phase_gaps:
                phase_gaps[gap.phase] = []
            phase_gaps[gap.phase].append(gap)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_capabilities': len(self.capabilities),
            'total_gaps': len(self.gaps),
            'severity_breakdown': severity_counts,
            'capabilities': [
                {
                    'name': cap.name,
                    'module': cap.module,
                    'status': cap.status,
                    'health': cap.health_score,
                    'methods': len(cap.methods)
                }
                for cap in self.capabilities.values()
            ],
            'gaps': [
                {
                    'id': gap.gap_id,
                    'requirement': gap.requirement,
                    'status': gap.current_status,
                    'severity': gap.severity,
                    'phase': gap.phase,
                    'effort': gap.estimated_effort
                }
                for gap in self.gaps
            ],
            'phase_breakdown': {
                phase: len(gaps) for phase, gaps in phase_gaps.items()
            }
        }
    
    def get_next_priority_gap(self) -> Optional[Gap]:
        """Get the highest priority gap to fix next"""
        if self.gaps:
            return self.gaps[0]  # Already sorted by severity
        return None
