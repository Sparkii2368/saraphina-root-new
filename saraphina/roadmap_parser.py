#!/usr/bin/env python3
"""
RoadmapParser - Parse roadmap.txt into structured goals and phases
"""
import re
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("RoadmapParser")


@dataclass
class Phase:
    """Represents a phase in the roadmap"""
    id: str
    name: str
    goal: str
    timeline: str
    deliverables: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    acceptance: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Roadmap:
    """Complete parsed roadmap"""
    phases: List[Phase] = field(default_factory=list)
    immediate_fixes: List[Dict[str, str]] = field(default_factory=list)
    core_schemas: List[str] = field(default_factory=list)
    quick_tasks: List[str] = field(default_factory=list)


class RoadmapParser:
    """Parse roadmap documents into structured actionable data"""
    
    def __init__(self):
        self.roadmap = Roadmap()
    
    def parse_file(self, file_path: str) -> Roadmap:
        """Parse roadmap from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_text(content)
        except Exception as e:
            logger.error(f"Failed to parse roadmap file: {e}")
            return Roadmap()
    
    def parse_text(self, content: str) -> Roadmap:
        """Parse roadmap from text content"""
        self.roadmap = Roadmap()
        
        # Split into sections
        sections = self._split_sections(content)
        
        # Parse phases - more flexible pattern
        phase_pattern = re.compile(
            r'Phase\s+([A-Z])\s*[—\-–]\s*(.+?)\s*\((.+?)\)',
            re.IGNORECASE
        )
        
        for match in phase_pattern.finditer(content):
            try:
                phase_id = match.group(1)
                name = match.group(2).strip()
                timeline = match.group(3).strip()
                
                # Try to find goal after this match
                goal_match = re.search(r'Goal:\s*(.+?)(?=\n\n|Deliverables:|Phase)', 
                                      content[match.end():match.end()+500], 
                                      re.IGNORECASE | re.DOTALL)
                goal = goal_match.group(1).strip() if goal_match else name
                
                phase = Phase(
                    id=phase_id,
                    name=name,
                    goal=goal,
                    timeline=timeline
                )
                
                # Extract deliverables
                phase.deliverables = self._extract_deliverables(content, match.end())
                
                # Extract commands
                phase.commands = self._extract_commands(content, match.end())
                
                # Extract acceptance criteria
                phase.acceptance = self._extract_acceptance(content, match.end())
                
                self.roadmap.phases.append(phase)
            except Exception as e:
                logger.debug(f"Failed to parse phase {match.group(1)}: {e}")
                continue
        
        # Parse immediate fixes
        self.roadmap.immediate_fixes = self._extract_immediate_fixes(content)
        
        # Parse core schemas
        self.roadmap.core_schemas = self._extract_schemas(content)
        
        # Parse quick tasks
        self.roadmap.quick_tasks = self._extract_quick_tasks(content)
        
        logger.info(f"Parsed roadmap: {len(self.roadmap.phases)} phases, "
                   f"{len(self.roadmap.immediate_fixes)} fixes, "
                   f"{len(self.roadmap.core_schemas)} schemas")
        
        return self.roadmap
    
    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split content into major sections"""
        sections = {}
        current_section = "main"
        current_content = []
        
        for line in content.split('\n'):
            if re.match(r'^[A-Z][A-Za-z\s]+$', line.strip()) and len(line.strip()) > 5:
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.strip().lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_deliverables(self, content: str, start_pos: int) -> List[str]:
        """Extract deliverables from phase section"""
        deliverables = []
        
        # Find deliverables section
        match = re.search(r'Deliverables:\s*\n(.*?)(?=\n(?:Commands:|Acceptance:|Phase|$))', 
                         content[start_pos:start_pos+2000], re.DOTALL | re.IGNORECASE)
        
        if match:
            deliv_text = match.group(1)
            # Extract bullet points
            for line in deliv_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 
                           re.match(r'^\d+\.', line)):
                    # Clean up the bullet
                    cleaned = re.sub(r'^[-•\d.)\s]+', '', line).strip()
                    if cleaned:
                        deliverables.append(cleaned)
        
        return deliverables
    
    def _extract_commands(self, content: str, start_pos: int) -> List[str]:
        """Extract slash commands from phase section"""
        commands = []
        
        match = re.search(r'Commands?:\s*([^\n]+)', 
                         content[start_pos:start_pos+1000], re.IGNORECASE)
        
        if match:
            cmd_text = match.group(1)
            # Extract /command patterns
            commands = re.findall(r'/[\w-]+(?:\s+<[\w_]+>)?', cmd_text)
        
        return commands
    
    def _extract_acceptance(self, content: str, start_pos: int) -> str:
        """Extract acceptance criteria"""
        match = re.search(r'Acceptance:\s*(.+?)(?=\n\n|Phase|$)', 
                         content[start_pos:start_pos+1000], re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_immediate_fixes(self, content: str) -> List[Dict[str, str]]:
        """Extract immediate fixes section"""
        fixes = []
        
        # Find immediate fixes section
        match = re.search(r'Immediate fixes.*?\n(.*?)(?=\n[A-Z][a-z]+\s+[a-z]+|$)', 
                         content, re.DOTALL | re.IGNORECASE)
        
        if match:
            fix_text = match.group(1)
            # Extract each fix with Fix: and Acceptance:
            fix_pattern = re.compile(r'(.+?)\s*Fix:\s*(.+?)\s*Acceptance:\s*(.+?)(?=\n\n|\n[A-Z]|$)', 
                                    re.DOTALL)
            
            for fix_match in fix_pattern.finditer(fix_text):
                fixes.append({
                    'issue': fix_match.group(1).strip(),
                    'fix': fix_match.group(2).strip(),
                    'acceptance': fix_match.group(3).strip()
                })
        
        return fixes
    
    def _extract_schemas(self, content: str) -> List[str]:
        """Extract core data schemas"""
        schemas = []
        
        match = re.search(r'Core data schemas\s*\n(.*?)(?=\n[A-Z][a-z]+\s+[a-z]+|$)', 
                         content, re.DOTALL | re.IGNORECASE)
        
        if match:
            schema_text = match.group(1)
            # Extract schema definitions
            for line in schema_text.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    schemas.append(line)
        
        return schemas
    
    def _extract_quick_tasks(self, content: str) -> List[str]:
        """Extract quick-start tasks"""
        tasks = []
        
        match = re.search(r'Quick[- ]start tasks.*?\n(.*?)(?=$)', 
                         content, re.DOTALL | re.IGNORECASE)
        
        if match:
            task_text = match.group(1)
            # Extract numbered or bulleted tasks
            for line in task_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or re.match(r'^\d+\.', line)):
                    cleaned = re.sub(r'^[-•\d.)\s]+', '', line).strip()
                    if cleaned and ':' in cleaned:
                        tasks.append(cleaned)
        
        return tasks
    
    def get_phase(self, phase_id: str) -> Phase:
        """Get specific phase by ID"""
        for phase in self.roadmap.phases:
            if phase.id.upper() == phase_id.upper():
                return phase
        return None
    
    def get_all_deliverables(self) -> List[str]:
        """Get flat list of all deliverables across phases"""
        all_delivs = []
        for phase in self.roadmap.phases:
            all_delivs.extend(phase.deliverables)
        return all_delivs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert roadmap to dictionary"""
        return {
            'phases': [
                {
                    'id': p.id,
                    'name': p.name,
                    'goal': p.goal,
                    'timeline': p.timeline,
                    'deliverables': p.deliverables,
                    'commands': p.commands,
                    'acceptance': p.acceptance
                }
                for p in self.roadmap.phases
            ],
            'immediate_fixes': self.roadmap.immediate_fixes,
            'core_schemas': self.roadmap.core_schemas,
            'quick_tasks': self.roadmap.quick_tasks
        }
