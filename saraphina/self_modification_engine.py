#!/usr/bin/env python3
"""
SelfModificationEngine - Analyze and improve Saraphina's own codebase.

CRITICAL SAFETY: All modifications require explicit owner approval.
Creates reversible patches with full audit trail.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import ast
import difflib
import hashlib
import json
import subprocess
import sys

from .code_risk_model import CodeRiskModel
from .owner_approval_gate import OwnerApprovalGate
from .code_audit_trail import CodeAuditTrail

try:
    from .ai_risk_analyzer import AIRiskAnalyzer
    AI_RISK_AVAILABLE = True
except (ImportError, ValueError):
    # OpenAI not available or no API key
    AI_RISK_AVAILABLE = False
    AIRiskAnalyzer = None


class SelfModificationEngine:
    """Propose and apply improvements to Saraphina's codebase."""
    
    def __init__(self, code_factory, proposal_db, security_manager, db):
        """
        Initialize self-modification engine.
        
        Args:
            code_factory: CodeFactory for generating improvements
            proposal_db: CodeProposalDB for tracking changes
            security_manager: SecurityManager for audit logging
            db: Database connection for audit trail
        """
        self.code_factory = code_factory
        self.proposal_db = proposal_db
        self.security = security_manager
        self.saraphina_root = Path(__file__).parent
        self.max_file_size = 50000  # 50KB max per file
        
        # Phase 30: Enhanced safety
        self.risk_model = CodeRiskModel()
        self.approval_gate = OwnerApprovalGate(self.saraphina_root / 'data' / 'approvals')
        self.audit_trail = CodeAuditTrail(db)
        
        # Phase 30.5: AI-powered risk analysis (optional)
        self.ai_risk_analyzer = None
        if AI_RISK_AVAILABLE:
            try:
                self.ai_risk_analyzer = AIRiskAnalyzer()
            except Exception as e:
                # Fall back to regex-based if AI setup fails
                pass
    
    def scan_codebase(
        self,
        target_module: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scan Saraphina's codebase for improvement opportunities.
        
        Args:
            target_module: Specific module to scan (e.g., 'code_factory')
        
        Returns:
            Dict with opportunities, file analysis, metrics
        """
        opportunities = []
        scanned_files = []
        
        # Get all Python files
        if target_module:
            files = [self.saraphina_root / f"{target_module}.py"]
        else:
            files = list(self.saraphina_root.glob("*.py"))
        
        for file_path in files:
            if not file_path.exists() or file_path.stat().st_size > self.max_file_size:
                continue
            
            try:
                analysis = self._analyze_file(file_path)
                scanned_files.append(analysis)
                
                # Find improvement opportunities
                if analysis.get('issues'):
                    for issue in analysis['issues']:
                        if issue['severity'] in ['high', 'medium']:
                            opportunities.append({
                                'file': file_path.name,
                                'type': issue['type'],
                                'severity': issue['severity'],
                                'description': issue['description'],
                                'line': issue.get('line')
                            })
            
            except Exception as e:
                scanned_files.append({
                    'file': file_path.name,
                    'error': str(e)
                })
        
        return {
            'scanned_files': len(scanned_files),
            'opportunities': opportunities,
            'file_analyses': scanned_files,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        content = file_path.read_text(encoding='utf-8')
        
        analysis = {
            'file': file_path.name,
            'lines': len(content.splitlines()),
            'size_bytes': len(content),
            'issues': []
        }
        
        # Parse AST for structure analysis
        try:
            tree = ast.parse(content)
            analysis['functions'] = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            analysis['classes'] = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            
            # Check for common issues
            for node in ast.walk(tree):
                # Missing docstrings
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        analysis['issues'].append({
                            'type': 'missing_docstring',
                            'severity': 'low',
                            'description': f'{node.__class__.__name__} {node.name} lacks docstring',
                            'line': node.lineno
                        })
                
                # Long functions (>50 lines)
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        analysis['issues'].append({
                            'type': 'long_function',
                            'severity': 'medium',
                            'description': f'Function {node.name} has {func_lines} lines (consider refactoring)',
                            'line': node.lineno
                        })
                
                # Broad exception handling
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception'):
                        analysis['issues'].append({
                            'type': 'broad_except',
                            'severity': 'low',
                            'description': 'Catching broad exception (consider specific exceptions)',
                            'line': node.lineno
                        })
        
        except SyntaxError as e:
            analysis['issues'].append({
                'type': 'syntax_error',
                'severity': 'high',
                'description': f'Syntax error: {e.msg}',
                'line': e.lineno
            })
        
        return analysis
    
    def propose_improvement(
        self,
        target_file: str,
        improvement_spec: str,
        safety_level: str = 'high'
    ) -> Dict[str, Any]:
        """
        Propose an improvement to a Saraphina module.
        
        Args:
            target_file: Module file to improve (e.g., 'code_factory.py')
            improvement_spec: Description of desired improvement
            safety_level: 'high' (requires tests), 'medium', 'low'
        
        Returns:
            Dict with proposal_id, original code, improved code, diff, safety checks
        """
        file_path = self.saraphina_root / target_file
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f'File not found: {target_file}'
            }
        
        # Read current code
        original_code = file_path.read_text(encoding='utf-8')
        
        # Safety check: File hash for integrity
        original_hash = hashlib.sha256(original_code.encode()).hexdigest()
        
        # Generate improvement using GPT-4o
        context = {
            'existing_code': original_code,
            'constraints': f'Maintain backward compatibility. Safety level: {safety_level}.',
            'requirements': 'Preserve all existing functionality. Add improvements incrementally.'
        }
        
        proposal = self.code_factory.propose_code(
            feature_spec=f"Improve {target_file}: {improvement_spec}",
            language='python',
            context=context
        )
        
        if not proposal.get('success'):
            return {
                'success': False,
                'error': 'Code generation failed',
                'details': proposal
            }
        
        improved_code = proposal['code']
        
        # Generate diff
        diff = self._generate_diff(original_code, improved_code, target_file)
        
        # Phase 30.5: Hybrid risk classification (AI + Regex)
        risk_classification = self._classify_patch_hybrid(
            original_code,
            improved_code,
            target_file,
            improvement_spec
        )
        
        # Safety checks
        safety_checks = self._run_safety_checks(
            original_code,
            improved_code,
            file_path,
            safety_level
        )
        
        # Merge risk info into safety checks
        safety_checks['risk_classification'] = risk_classification
        safety_checks['requires_owner_approval'] = self.risk_model.requires_owner_approval(risk_classification)
        
        # Store as special self-modification proposal
        proposal_id = f"selfmod_{proposal['proposal_id']}"
        
        self_mod_proposal = {
            'proposal_id': proposal_id,
            'feature_spec': f'[SELF-MOD] {target_file}: {improvement_spec}',
            'language': 'python',
            'code': improved_code,
            'tests': proposal.get('tests', ''),
            'explanation': proposal.get('explanation', ''),
            'related_concepts': proposal.get('related_concepts', []),
            'metadata': {
                'target_file': target_file,
                'original_hash': original_hash,
                'safety_level': safety_level,
                'safety_checks': safety_checks,
                'diff': diff
            }
        }
        
        # Store in database
        self.proposal_db.store_proposal(self_mod_proposal)
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'target_file': target_file,
            'original_code': original_code,
            'improved_code': improved_code,
            'diff': diff,
            'safety_checks': safety_checks,
            'requires_approval': True,
            'warning': 'SELF-MODIFICATION: Owner approval required before applying'
        }
    
    def _generate_diff(
        self,
        original: str,
        improved: str,
        filename: str
    ) -> str:
        """Generate unified diff."""
        original_lines = original.splitlines(keepends=True)
        improved_lines = improved.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            improved_lines,
            fromfile=f'a/{filename}',
            tofile=f'b/{filename}',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def _run_safety_checks(
        self,
        original: str,
        improved: str,
        file_path: Path,
        safety_level: str
    ) -> Dict[str, Any]:
        """Run comprehensive safety checks."""
        checks = {
            'passed': True,
            'warnings': [],
            'errors': []
        }
        
        # 1. Syntax check
        try:
            ast.parse(improved)
            checks['syntax_valid'] = True
        except SyntaxError as e:
            checks['syntax_valid'] = False
            checks['errors'].append(f'Syntax error: {e.msg} at line {e.lineno}')
            checks['passed'] = False
        
        # 2. Check imports don't change drastically
        orig_imports = self._extract_imports(original)
        new_imports = self._extract_imports(improved)
        
        removed_imports = orig_imports - new_imports
        if removed_imports:
            checks['warnings'].append(f'Imports removed: {removed_imports}')
        
        # 3. Check critical functions preserved
        orig_funcs = self._extract_function_names(original)
        new_funcs = self._extract_function_names(improved)
        
        removed_funcs = orig_funcs - new_funcs
        if removed_funcs:
            checks['errors'].append(f'Functions removed: {removed_funcs}')
            checks['passed'] = False
        
        # 4. Size check (prevent massive bloat)
        size_change = len(improved) / len(original) if len(original) > 0 else 1
        if size_change > 2.0:
            checks['warnings'].append(f'Code size increased by {(size_change - 1) * 100:.0f}%')
        
        # 5. Check for dangerous patterns
        dangerous_patterns = ['os.system', 'exec(', 'eval(', '__import__']
        for pattern in dangerous_patterns:
            if pattern in improved and pattern not in original:
                checks['errors'].append(f'Dangerous pattern introduced: {pattern}')
                checks['passed'] = False
        
        checks['safety_level'] = safety_level
        return checks
    
    def _extract_imports(self, code: str) -> set:
        """Extract all import statements."""
        imports = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.add(node.module or '')
        except Exception:
            pass
        return imports
    
    def _extract_function_names(self, code: str) -> set:
        """Extract all function names."""
        functions = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.add(node.name)
        except Exception:
            pass
        return functions
    
    def apply_improvement(
        self,
        proposal_id: str,
        user_approval_phrase: Optional[str] = None,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Apply approved self-modification with Phase 30 safety.
        
        CRITICAL: This modifies Saraphina's source code!
        
        Args:
            proposal_id: ID of approved self-modification proposal
            user_approval_phrase: Owner approval phrase for risky changes
            create_backup: Create backup before applying
        
        Returns:
            Dict with success status, backup location, applied changes
        """
        proposal = self.proposal_db.get_proposal(proposal_id)
        
        if not proposal:
            return {'success': False, 'error': 'Proposal not found'}
        
        if proposal['status'] != 'approved':
            return {
                'success': False,
                'error': f'Proposal not approved (status: {proposal["status"]})'
            }
        
        # Extract metadata
        metadata = json.loads(proposal.get('related_concepts', '[]'))  # Stored as JSON
        if isinstance(metadata, list):
            return {'success': False, 'error': 'Invalid self-modification proposal'}
        
        target_file = metadata.get('target_file')
        original_hash = metadata.get('original_hash')
        
        if not target_file:
            return {'success': False, 'error': 'No target file in proposal'}
        
        file_path = self.saraphina_root / target_file
        
        # Verify file hasn't changed
        current_code = file_path.read_text(encoding='utf-8')
        current_hash = hashlib.sha256(current_code.encode()).hexdigest()
        
        if current_hash != original_hash:
            return {
                'success': False,
                'error': 'File has been modified since proposal created',
                'warning': 'Regenerate proposal with current code'
            }
        
        # Phase 30: Check risk and owner approval
        improved_code = proposal['code']
        risk_classification = self.risk_model.classify_patch(
            current_code,
            improved_code,
            target_file
        )
        
        # Check if owner approval required
        if self.risk_model.requires_owner_approval(risk_classification):
            # Check approval gate
            if not user_approval_phrase:
                # Request approval
                required_phrase = self.approval_gate.request_approval(
                    proposal_id,
                    risk_classification,
                    {'file_path': target_file, 'description': proposal.get('feature_spec', 'N/A')}
                )
                return {
                    'success': False,
                    'requires_approval': True,
                    'approval_request': self.approval_gate.format_approval_request(
                        proposal_id,
                        risk_classification,
                        {'file_path': target_file, 'description': proposal.get('feature_spec', 'N/A')}
                    )
                }
            
            # Verify approval phrase
            approval_result = self.approval_gate.verify_approval(proposal_id, user_approval_phrase)
            if not approval_result['approved']:
                # Log failed approval
                self.audit_trail.log_modification_attempt(
                    action='apply_improvement',
                    file_path=target_file,
                    patch_id=proposal_id,
                    risk_classification=risk_classification,
                    original_code=current_code,
                    modified_code=improved_code,
                    success=False,
                    error_message=f"Owner approval denied: {approval_result['reason']}"
                )
                return {
                    'success': False,
                    'error': f"Owner approval denied: {approval_result['reason']}"
                }
        
        # Create backup
        backup_path = None
        if create_backup:
            backup_dir = self.saraphina_root / 'backups' / 'self_mod'
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f'{target_file}.{timestamp}.backup'
            backup_path.write_text(current_code, encoding='utf-8')
        
        try:
            # Apply improved code
            file_path.write_text(improved_code, encoding='utf-8')
            
            # Phase 30: Log to immutable audit trail
            approved_by = 'owner' if user_approval_phrase else 'auto'
            self.audit_trail.log_modification_attempt(
                action='apply_improvement',
                file_path=target_file,
                patch_id=proposal_id,
                risk_classification=risk_classification,
                original_code=current_code,
                modified_code=improved_code,
                approved_by=approved_by,
                approval_phrase=user_approval_phrase,
                success=True,
                details={
                    'backup': str(backup_path) if backup_path else None,
                    'original_hash': original_hash,
                    'new_hash': hashlib.sha256(improved_code.encode()).hexdigest()
                }
            )
            
            # Clear pending approval
            self.approval_gate.clear_pending(proposal_id)
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'target_file': target_file,
                'backup_path': str(backup_path) if backup_path else None,
                'applied_at': datetime.now().isoformat(),
                'risk_level': risk_classification['risk_level'],
                'warning': 'RESTART REQUIRED: Changes take effect on next launch'
            }
        
        except Exception as e:
            # Rollback on error
            if backup_path and backup_path.exists():
                file_path.write_text(backup_path.read_text(), encoding='utf-8')
            
            # Phase 30: Log failure
            self.audit_trail.log_modification_attempt(
                action='apply_improvement',
                file_path=target_file,
                patch_id=proposal_id,
                risk_classification=risk_classification,
                original_code=current_code,
                modified_code=improved_code,
                success=False,
                error_message=str(e),
                details={'rolled_back': True}
            )
            
            return {
                'success': False,
                'error': f'Application failed: {e}',
                'rolled_back': True
            }
    
    def _classify_patch_hybrid(
        self,
        original: str,
        modified: str,
        file_name: str,
        context_description: str = ''
    ) -> Dict[str, Any]:
        """
        Phase 30.5: Hybrid risk classification using AI + regex.
        
        Uses AI analysis when available, falls back to regex,
        and combines insights from both.
        """
        # Always get regex-based analysis as baseline
        regex_result = self.risk_model.classify_patch(original, modified, file_name)
        
        # If AI available, use it for enhanced analysis
        if self.ai_risk_analyzer:
            try:
                context = {'purpose': context_description}
                ai_result = self.ai_risk_analyzer.analyze_patch(
                    original,
                    modified,
                    file_name,
                    context
                )
                
                # Combine results: use AI's risk level if more cautious or if high confidence
                if ai_result.get('confidence', 0) > 0.7:
                    # High confidence: trust AI
                    combined = ai_result.copy()
                    combined['regex_flags'] = regex_result.get('flags', [])
                    combined['analysis_method'] = 'ai_primary'
                elif self._risk_level_value(ai_result['risk_level']) > self._risk_level_value(regex_result['risk_level']):
                    # AI more cautious: use AI but note uncertainty
                    combined = ai_result.copy()
                    combined['regex_flags'] = regex_result.get('flags', [])
                    combined['analysis_method'] = 'ai_conservative'
                else:
                    # Use regex but add AI insights
                    combined = regex_result.copy()
                    combined['ai_reasoning'] = ai_result.get('reasoning', '')
                    combined['ai_recommendations'] = ai_result.get('recommendations', [])
                    combined['analysis_method'] = 'regex_with_ai_insights'
                
                return combined
            
            except Exception as e:
                # AI failed, use regex
                regex_result['ai_error'] = str(e)
                regex_result['analysis_method'] = 'regex_fallback'
                return regex_result
        else:
            # No AI available
            regex_result['analysis_method'] = 'regex_only'
            return regex_result
    
    def _risk_level_value(self, level: str) -> int:
        """Convert risk level to numeric value."""
        levels = {'SAFE': 0, 'CAUTION': 1, 'SENSITIVE': 2, 'CRITICAL': 3}
        return levels.get(level, 1)
    
    def ethics_check_code(self, code_snippet: str, file_name: str = 'unknown.py') -> str:
        """
        Phase 30: Check code for ethical/safety concerns.
        
        Args:
            code_snippet: Code to analyze
            file_name: Name of file (for context)
        
        Returns:
            Formatted risk report
        """
        # Use empty original to focus on new code
        risk_classification = self.risk_model.classify_patch(
            '',
            code_snippet,
            file_name
        )
        
        return self.risk_model.format_risk_report(risk_classification)
    
    def get_audit_history(
        self,
        file_path: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        Phase 30: Get modification audit history.
        
        Args:
            file_path: Filter by file
            risk_level: Filter by risk (SAFE, CAUTION, SENSITIVE, CRITICAL)
            limit: Max entries
        
        Returns:
            Formatted audit report
        """
        entries = self.audit_trail.get_modification_history(
            file_path=file_path,
            risk_level=risk_level,
            limit=limit
        )
        
        return self.audit_trail.format_audit_report(entries)
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Phase 30: Get audit trail statistics."""
        return self.audit_trail.get_statistics()
    
    def get_pending_approvals(self) -> str:
        """Phase 30: Get pending approval requests."""
        pending = self.approval_gate.get_pending_approvals()
        
        if not pending:
            return "No pending approval requests."
        
        report = f"📋 Pending Approvals ({len(pending)})\n\n"
        for patch_id, details in pending.items():
            risk = details['risk_classification']['risk_level']
            file_path = details['patch_details'].get('file_path', 'Unknown')
            report += f"• {patch_id}\n"
            report += f"  File: {file_path}\n"
            report += f"  Risk: {risk}\n"
            report += f"  Requested: {details['requested_at'][:19]}\n\n"
        
        return report
    
    def rollback_improvement(
        self,
        backup_path: str
    ) -> Dict[str, Any]:
        """Rollback to backup."""
        backup = Path(backup_path)
        
        if not backup.exists():
            return {'success': False, 'error': 'Backup not found'}
        
        # Extract original filename
        target_file = backup.stem.split('.')[0] + '.py'
        file_path = self.saraphina_root / target_file
        
        try:
            backup_content = backup.read_text(encoding='utf-8')
            current_code = file_path.read_text(encoding='utf-8')
            file_path.write_text(backup_content, encoding='utf-8')
            
            # Phase 30: Log rollback
            self.audit_trail.log_modification_attempt(
                action='rollback',
                file_path=target_file,
                original_code=current_code,
                modified_code=backup_content,
                success=True,
                approved_by='owner',
                details={'backup_path': str(backup)}
            )
            
            return {
                'success': True,
                'target_file': target_file,
                'restored_from': str(backup),
                'warning': 'RESTART REQUIRED'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
