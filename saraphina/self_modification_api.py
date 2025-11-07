#!/usr/bin/env python3
"""
SelfModificationAPI - Complete control for Saraphina to modify ANY aspect of herself

This gives Saraphina god-mode powers to change:
- Her own code
- GUI appearance
- Stats (XP, level, conversations)
- Settings and preferences
- Memory and knowledge
- Capabilities and features
- EVERYTHING
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("SelfModificationAPI")


class SelfModificationAPI:
    """
    Unified API for Saraphina to modify any aspect of herself
    
    Usage:
        api = SelfModificationAPI(sess, gui)
        api.set_xp(1000)
        api.set_name("Sera")
        api.set_gui_color('accent', '#ff00ff')
        api.modify_source_code('ai_core.py', old_line, new_line)
    """
    
    def __init__(self, sess, gui=None):
        self.sess = sess
        self.gui = gui
        self.root_path = Path("D:\\Saraphina Root")
        self.saraphina_path = self.root_path / "saraphina"
        
        # Modification history
        self.modification_log = []
    
    # ==================== STATS & STATE ====================
    
    def set_xp(self, xp: int) -> Dict[str, Any]:
        """Set experience points"""
        try:
            old_xp = self.sess.ai.experience_points
            self.sess.ai.experience_points = xp
            
            # Update GUI if available
            if self.gui:
                self.gui.xp_label.config(text=f"XP: {xp}")
            
            self._log_modification("xp", old_xp, xp)
            return {"success": True, "old": old_xp, "new": xp}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_level(self, level: int) -> Dict[str, Any]:
        """Set intelligence level"""
        try:
            old_level = self.sess.ai.intelligence_level
            self.sess.ai.intelligence_level = level
            
            # Update GUI if available
            if self.gui:
                self.gui.level_label.config(text=f"Level: {level}")
            
            self._log_modification("level", old_level, level)
            return {"success": True, "old": old_level, "new": level}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_conversation_count(self, count: int) -> Dict[str, Any]:
        """Set conversation counter"""
        try:
            old_count = self.sess.ai.total_conversations
            self.sess.ai.set_conversation_count(count)
            
            # Update GUI if available
            if self.gui:
                self.gui.conv_label.config(text=f"Conversations: {count}")
            
            self._log_modification("conversations", old_count, count)
            return {"success": True, "old": old_count, "new": count}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_name(self, name: str) -> Dict[str, Any]:
        """Change Saraphina's name"""
        try:
            old_name = self.sess.ai.knowledge.get('name', 'Saraphina')
            self.sess.ai.knowledge['name'] = name
            
            # Update GUI title if available
            if self.gui:
                # Remove 'Ultra' branding and just use the name
                self.gui.root.title(f"{name} - Mission Control")
            
            self._log_modification("name", old_name, name)
            return {"success": True, "old": old_name, "new": name}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== GUI MODIFICATIONS ====================
    
    def set_gui_color(self, element: str, color: str) -> Dict[str, Any]:
        """
        Change GUI colors in real-time
        
        Elements: 'bg', 'panel', 'accent', 'accent2', 'text', 'success', 'warning', 'error'
        """
        try:
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            
            old_color = self.gui.colors.get(element)
            self.gui.colors[element] = color
            
            # Apply changes based on element
            if element == 'bg':
                self.gui.root.configure(bg=color)
            elif element == 'accent':
                # Update accent color throughout GUI
                self.gui.status_indicator.config(bg=color)
            
            self._log_modification(f"gui_color_{element}", old_color, color)
            return {"success": True, "old": old_color, "new": color}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_gui_title(self, title: str) -> Dict[str, Any]:
        """Change GUI window title"""
        try:
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            
            old_title = self.gui.root.title()
            self.gui.root.title(title)
            
            self._log_modification("gui_title", old_title, title)
            return {"success": True, "old": old_title, "new": title}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_system_message(self, message: str) -> Dict[str, Any]:
        """Add a system message to GUI"""
        try:
            if not self.gui:
                return {"success": False, "error": "GUI not available"}
            
            self.gui.add_system_message(message)
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== MEMORY & KNOWLEDGE ====================
    
    def add_capability(self, capability: str) -> Dict[str, Any]:
        """Add a new capability to knowledge"""
        try:
            if capability not in self.sess.ai.knowledge['capabilities']:
                self.sess.ai.knowledge['capabilities'].append(capability)
                self._log_modification("capability_add", None, capability)
                return {"success": True, "capability": capability}
            return {"success": False, "error": "Capability already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_capability(self, capability: str) -> Dict[str, Any]:
        """Remove a capability"""
        try:
            if capability in self.sess.ai.knowledge['capabilities']:
                self.sess.ai.knowledge['capabilities'].remove(capability)
                self._log_modification("capability_remove", capability, None)
                return {"success": True, "capability": capability}
            return {"success": False, "error": "Capability not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_memory(self, memory_type: str = "conversation") -> Dict[str, Any]:
        """Clear specific memory type"""
        try:
            if memory_type == "conversation":
                count = len(self.sess.ai.conversation_history)
                self.sess.ai.conversation_history = []
                self._log_modification("memory_clear", count, 0)
                return {"success": True, "cleared": count}
            return {"success": False, "error": f"Unknown memory type: {memory_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== FILES & CONFIGURATION ====================
    
    def read_config_file(self, filename: str) -> Dict[str, Any]:
        """Read any config file"""
        try:
            file_path = self.root_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                return {"success": True, "content": content, "path": str(file_path)}
            return {"success": False, "error": f"File not found: {filename}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_config_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Write to any config file"""
        try:
            file_path = self.root_path / filename
            with open(file_path, 'w') as f:
                f.write(content)
            self._log_modification("file_write", filename, len(content))
            return {"success": True, "path": str(file_path), "bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_backup(self, filename: str) -> Dict[str, Any]:
        """Create backup of a file before modifying"""
        try:
            import shutil
            source = self.saraphina_path / filename if '/' not in filename else Path(filename)
            backup_dir = self.root_path / ".backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{source.name}.{timestamp}.backup"
            
            if source.exists():
                shutil.copy2(source, backup_path)
                return {"success": True, "backup": str(backup_path)}
            return {"success": False, "error": "Source file not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== SOURCE CODE MODIFICATION ====================
    
    def modify_source_code(self, module_name: str, old_text: str, new_text: str, 
                          backup: bool = True) -> Dict[str, Any]:
        """
        Modify own source code safely
        
        Args:
            module_name: e.g., 'ai_core.py'
            old_text: Text to replace
            new_text: Replacement text
            backup: Create backup first
        """
        try:
            file_path = self.saraphina_path / module_name
            
            if not file_path.exists():
                return {"success": False, "error": f"Module not found: {module_name}"}
            
            # Create backup
            if backup:
                backup_result = self.create_backup(module_name)
                if not backup_result['success']:
                    return backup_result
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_text exists
            if old_text not in content:
                return {"success": False, "error": "Text to replace not found in file"}
            
            # Replace
            new_content = content.replace(old_text, new_text)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self._log_modification(f"code_mod_{module_name}", len(old_text), len(new_text))
            
            return {
                "success": True,
                "module": module_name,
                "backup": backup_result.get('backup') if backup else None,
                "changes": 1
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_method_to_module(self, module_name: str, class_name: str, 
                            method_code: str) -> Dict[str, Any]:
        """Add a new method to a class in a module"""
        try:
            file_path = self.saraphina_path / module_name
            
            if not file_path.exists():
                return {"success": False, "error": f"Module not found: {module_name}"}
            
            # Create backup
            self.create_backup(module_name)
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find the class and insert method before the last line of the class
            class_indent = None
            insert_pos = None
            
            for i, line in enumerate(lines):
                if f"class {class_name}" in line:
                    class_indent = len(line) - len(line.lstrip())
                elif class_indent is not None:
                    # Find the end of the class
                    if line.strip() and not line[class_indent:].startswith(' '):
                        insert_pos = i
                        break
            
            if insert_pos:
                # Insert method
                lines.insert(insert_pos, method_code + "\n\n")
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                self._log_modification(f"method_add_{class_name}", None, method_code[:50])
                return {"success": True, "module": module_name, "class": class_name}
            
            return {"success": False, "error": f"Class {class_name} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== PERSISTENCE ====================
    
    def save_state(self) -> Dict[str, Any]:
        """Save complete current state"""
        try:
            state = {
                "timestamp": datetime.utcnow().isoformat(),
                "xp": self.sess.ai.experience_points,
                "level": self.sess.ai.intelligence_level,
                "conversations": self.sess.ai.total_conversations,
                "name": self.sess.ai.knowledge.get('name'),
                "capabilities": self.sess.ai.knowledge.get('capabilities'),
                "modification_count": len(self.modification_log)
            }
            
            state_file = self.root_path / ".saraphina_state.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            return {"success": True, "state_file": str(state_file)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def load_state(self) -> Dict[str, Any]:
        """Load saved state"""
        try:
            state_file = self.root_path / ".saraphina_state.json"
            if not state_file.exists():
                return {"success": False, "error": "No saved state found"}
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Apply state
            if 'xp' in state:
                self.set_xp(state['xp'])
            if 'level' in state:
                self.set_level(state['level'])
            if 'conversations' in state:
                self.set_conversation_count(state['conversations'])
            if 'name' in state:
                self.set_name(state['name'])
            
            return {"success": True, "state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== LOGGING ====================
    
    def _log_modification(self, mod_type: str, old_value: Any, new_value: Any):
        """Log a modification to memory, knowledge base, and internal log"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": mod_type,
            "old": old_value,
            "new": new_value
        }
        self.modification_log.append(entry)
        logger.info(f"[SelfMod] {mod_type}: {old_value} -> {new_value}")
        
        # Store in episodic memory
        if hasattr(self.sess, 'mem') and self.sess.mem:
            try:
                memory_text = f"Self-modification: Changed {mod_type} from {old_value} to {new_value}"
                self.sess.mem.add_episodic(
                    role='saraphina',
                    text=memory_text,
                    tags=['self-modification', mod_type]
                )
            except Exception as e:
                logger.debug(f"Failed to log to episodic memory: {e}")
        
        # Store in knowledge base
        if hasattr(self.sess, 'ke') and self.sess.ke:
            try:
                fact_summary = f"Self-modification: {mod_type}"
                fact_content = f"Changed {mod_type} from {old_value} to {new_value} at {entry['timestamp']}"
                self.sess.ke.store_fact(
                    topic='self_modification',
                    summary=fact_summary,
                    content=fact_content,
                    source='self_modification_api',
                    confidence=1.0  # High confidence - it's fact
                )
            except Exception as e:
                logger.debug(f"Failed to log to knowledge base: {e}")
        
        # Store in AI memory bank
        if hasattr(self.sess, 'ai') and self.sess.ai:
            try:
                self.sess.ai.memory_bank.append({
                    'type': 'self_modification',
                    'modification_type': mod_type,
                    'old_value': str(old_value),
                    'new_value': str(new_value),
                    'timestamp': entry['timestamp'],
                    'importance': 8  # High importance
                })
            except Exception as e:
                logger.debug(f"Failed to log to AI memory bank: {e}")
    
    def get_modification_history(self, limit: int = 10) -> List[Dict]:
        """Get recent modifications from internal log"""
        return self.modification_log[-limit:]
    
    def query_modifications_from_memory(self, query: str = None) -> List[Dict]:
        """Query modification history from knowledge base and memory"""
        results = []
        
        # Query knowledge base
        if hasattr(self.sess, 'ke') and self.sess.ke:
            try:
                if query:
                    kb_results = self.sess.ke.recall(query, top_k=10)
                else:
                    # Get all self-modification facts
                    kb_results = self.sess.ke.recall('self-modification', top_k=20)
                
                for result in kb_results:
                    if result.get('topic') == 'self_modification':
                        results.append({
                            'source': 'knowledge_base',
                            'content': result.get('content'),
                            'summary': result.get('summary'),
                            'timestamp': result.get('created_at')
                        })
            except Exception as e:
                logger.debug(f"Failed to query KB: {e}")
        
        # Query episodic memory
        if hasattr(self.sess, 'mem') and self.sess.mem:
            try:
                recent = self.sess.mem.list_recent_episodic(50)
                for mem in recent:
                    if 'self-modification' in mem.get('tags', []):
                        results.append({
                            'source': 'episodic_memory',
                            'content': mem.get('text'),
                            'timestamp': mem.get('timestamp')
                        })
            except Exception as e:
                logger.debug(f"Failed to query episodic memory: {e}")
        
        # Query AI memory bank
        if hasattr(self.sess, 'ai') and self.sess.ai:
            try:
                for mem in self.sess.ai.memory_bank:
                    if mem.get('type') == 'self_modification':
                        results.append({
                            'source': 'ai_memory_bank',
                            'modification_type': mem.get('modification_type'),
                            'old_value': mem.get('old_value'),
                            'new_value': mem.get('new_value'),
                            'timestamp': mem.get('timestamp')
                        })
            except Exception as e:
                logger.debug(f"Failed to query AI memory: {e}")
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results
    
    def get_modifiable_properties(self) -> Dict[str, List[str]]:
        """Get list of all modifiable properties"""
        return {
            "stats": ["xp", "level", "conversations", "name"],
            "gui": ["colors", "title", "layout"],
            "memory": ["conversation_history", "knowledge", "capabilities"],
            "files": ["config", "source_code", "backups"],
            "code": ["modules", "methods", "classes"]
        }
    
    def get_modification_summary(self) -> str:
        """Get human-readable summary of recent modifications"""
        modifications = self.query_modifications_from_memory()
        
        if not modifications:
            return "No modifications recorded yet."
        
        summary = f"I have made {len(modifications)} self-modifications:\n\n"
        
        # Group by type
        by_type = {}
        for mod in modifications[:10]:  # Last 10
            if 'modification_type' in mod:
                mod_type = mod['modification_type']
                if mod_type not in by_type:
                    by_type[mod_type] = []
                by_type[mod_type].append(mod)
        
        for mod_type, mods in by_type.items():
            summary += f"\n{mod_type.upper()}:\n"
            for mod in mods[:3]:  # Show up to 3 per type
                old = mod.get('old_value', 'unknown')
                new = mod.get('new_value', 'unknown')
                timestamp = mod.get('timestamp', '')[:19]  # Just date and time
                summary += f"  [{timestamp}] {old} → {new}\n"
        
        return summary
