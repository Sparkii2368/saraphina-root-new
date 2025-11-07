#!/usr/bin/env python3
"""
SelfModificationCoordinator - Orchestrates complete self-modification flow

Links user requests to actual code changes through:
1. Parse request → detect intent
2. Scan codebase → find targets
3. Generate spec → structured plan
4. Create patches → concrete changes
5. Validate → test before apply
6. Apply → atomic execution
7. Learn → pattern extraction

This is the "glue" that makes self-modification actually work.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModificationRequest:
    """Structured modification request"""
    intent: str  # 'replace_string', 'create_module', 'fix_error', 'refactor'
    description: str  # Original user request
    targets: List[str]  # Files to modify
    parameters: Dict[str, Any]  # Intent-specific params
    priority: str = "normal"  # 'low', 'normal', 'high', 'critical'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'intent': self.intent,
            'description': self.description,
            'targets': self.targets,
            'parameters': self.parameters,
            'priority': self.priority
        }


@dataclass
class ModificationPlan:
    """Complete plan for modification"""
    request: ModificationRequest
    spec: Any  # UpgradeSpec or ModuleSpec
    patches: List[Any]  # List of patches to apply
    validation_results: Dict[str, Any]
    estimated_risk: str  # 'low', 'medium', 'high'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request': self.request.to_dict(),
            'spec': getattr(self.spec, 'to_dict', lambda: str(self.spec))(),
            'num_patches': len(self.patches),
            'validation': self.validation_results,
            'risk': self.estimated_risk
        }


class SelfModificationCoordinator:
    """
    Coordinates all self-modification components.
    
    This is the "brain" that connects:
    - User request parsing
    - Codebase scanning
    - Patch generation
    - Validation
    - Application
    - Learning
    """
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina"):
        self.saraphina_root = Path(saraphina_root)
        
        # Initialize all components (lazy loading)
        self._scanner = None
        self._rewriter = None
        self._creator = None
        self._upgrader = None
        self._validator = None
        self._hot_reload = None
        self._learning_journal = None
        self._git = None
    
    @property
    def scanner(self):
        """Lazy load CodebaseScanner"""
        if self._scanner is None:
            from saraphina.codebase_scanner import CodebaseScanner
            self._scanner = CodebaseScanner()
        return self._scanner
    
    @property
    def rewriter(self):
        """Lazy load HardcodedStringRewriter"""
        if self._rewriter is None:
            from saraphina.hardcoded_string_rewriter import HardcodedStringRewriter
            self._rewriter = HardcodedStringRewriter()
        return self._rewriter
    
    @property
    def creator(self):
        """Lazy load ModuleCreator"""
        if self._creator is None:
            from saraphina.module_creator import ModuleCreator
            self._creator = ModuleCreator()
        return self._creator
    
    @property
    def upgrader(self):
        """Lazy load CodeUpgrader"""
        if self._upgrader is None:
            from saraphina.code_upgrader import CodeUpgrader
            self._upgrader = CodeUpgrader()
        return self._upgrader
    
    @property
    def validator(self):
        """Lazy load SandboxValidator"""
        if self._validator is None:
            from saraphina.sandbox_validator import SandboxValidator
            self._validator = SandboxValidator()
        return self._validator
    
    @property
    def hot_reload(self):
        """Lazy load HotReloadManager"""
        if self._hot_reload is None:
            from saraphina.hot_reload_manager import HotReloadManager
            self._hot_reload = HotReloadManager(str(self.saraphina_root))
        return self._hot_reload
    
    @property
    def learning_journal(self):
        """Lazy load LearningJournal"""
        if self._learning_journal is None:
            try:
                from saraphina.upgrade_learning_journal import LearningJournal
                self._learning_journal = LearningJournal()
            except Exception as e:
                logger.warning(f"Could not load LearningJournal: {e}")
        return self._learning_journal
    
    @property
    def git(self):
        """Lazy load GitIntegration"""
        if self._git is None:
            try:
                from saraphina.git_integration import GitIntegration
                self._git = GitIntegration()
            except Exception as e:
                logger.warning(f"Could not load GitIntegration: {e}")
        return self._git
    
    def parse_request(self, user_input: str) -> ModificationRequest:
        """
        Parse natural language request into structured ModificationRequest.
        
        Args:
            user_input: Natural language request from user
        
        Returns:
            ModificationRequest with detected intent
        """
        user_lower = user_input.lower()
        
        # Detect intent patterns
        intent = self._detect_intent(user_lower)
        
        # Extract parameters based on intent
        params = self._extract_parameters(user_input, intent)
        
        # Identify target files
        targets = self._identify_targets(user_lower, intent, params)
        
        # Assess priority
        priority = self._assess_priority(user_lower)
        
        return ModificationRequest(
            intent=intent,
            description=user_input,
            targets=targets,
            parameters=params,
            priority=priority
        )
    
    def _detect_intent(self, user_lower: str) -> str:
        """Detect user's intent from natural language"""
        
        # Replace/change string patterns
        if any(keyword in user_lower for keyword in ['remove', 'change', 'replace', 'rename', 'update']):
            if any(keyword in user_lower for keyword in ['ultra', 'name', 'title', 'header', 'text']):
                return 'replace_string'
        
        # Create module patterns
        if any(keyword in user_lower for keyword in ['create', 'add', 'build', 'make', 'implement']):
            if any(keyword in user_lower for keyword in ['module', 'class', 'function', 'feature']):
                return 'create_module'
        
        # Fix error patterns
        if any(keyword in user_lower for keyword in ['fix', 'repair', 'solve', 'debug']):
            return 'fix_error'
        
        # Refactor patterns
        if any(keyword in user_lower for keyword in ['refactor', 'extract', 'cleanup', 'optimize']):
            return 'refactor'
        
        # Global branding/page-wide update requests
        if any(kw in user_lower for kw in ['update all', 'all coding', 'every bit', 'global replace', 'remove ultra everywhere', 'remove ultra globally', 'rename brand globally']):
            return 'bulk_replace_branding'
        
        # Default to general upgrade
        return 'general_upgrade'
    
    def _extract_parameters(self, user_input: str, intent: str) -> Dict[str, Any]:
        """Extract parameters from request based on intent"""
        params = {}
        
        if intent == 'replace_string':
            text_lower = user_input.lower()
            # Heuristics for common commands like "remove ultra"
            if 'remove' in text_lower and 'ultra' in text_lower:
                # Remove the word ULTRA (case-insensitive, word boundaries only)
                params['old_value'] = r'(?i)\bULTRA\b'
                params['new_value'] = ''
                params['regex'] = True
                return params
            
            # Try to extract quoted remove pattern: remove "X"
            remove_match = re.search(r'remove\s+"([^"]+)"', user_input, re.IGNORECASE)
            if not remove_match:
                remove_match = re.search(r'remove\s+([A-Za-z0-9\s\-]+)', user_input)
            if remove_match:
                params['old_value'] = remove_match.group(1).strip()
                params['new_value'] = ''
                return params
            
            # Change/replace pattern
            change_match = re.search(
                r'(?:change|replace)\s+"([^"]+)"\s+(?:to|with)\s+"([^"]+)"',
                user_input,
                re.IGNORECASE
            )
            if not change_match:
                # Try without quotes
                change_match = re.search(
                    r'(?:change|replace)\s+([A-Za-z0-9\s\-]+?)\s+(?:to|with)\s+([A-Za-z0-9\s\-]+)',
                    user_input,
                    re.IGNORECASE
                )
            if change_match:
                params['old_value'] = change_match.group(1).strip()
                params['new_value'] = change_match.group(2).strip()
        
        elif intent == 'create_module':
            # Extract module name and description
            create_match = re.search(r'create\s+(?:a\s+)?(\w+)\s+module', user_input, re.IGNORECASE)
            if create_match:
                params['module_name'] = create_match.group(1)
                params['description'] = user_input
        
        return params
    
    def _identify_targets(self, user_lower: str, intent: str, params: Dict[str, Any]) -> List[str]:
        """Identify which files to target"""
        targets: List[str] = []
        project_root = self.saraphina_root.parent
        
        # GUI-related keywords → scan both package and project root
        if any(keyword in user_lower for keyword in ['gui', 'window', 'interface', 'display', 'title', 'header', 'name']):
            gui_candidates = list(self.saraphina_root.glob("*gui*.py")) + \
                             list(project_root.glob("*gui*.py"))
            targets.extend([str(f) for f in gui_candidates])
        
        # If replacing a specific string, scan for files containing it (both roots)
        if intent == 'replace_string' and 'old_value' in params:
            old_value = params['old_value']
            targets.extend(self._find_files_containing(old_value, search_root=self.saraphina_root))
            targets.extend(self._find_files_containing(old_value, search_root=project_root))
        
        # Always include known GUI files if they exist
        common_files = [
            project_root / 'saraphina_gui.py',
            self.saraphina_root / 'gui_ultra_processor.py',
            self.saraphina_root / 'ui_manager.py',
            self.saraphina_root / 'self_modification_api.py'
        ]
        for f in common_files:
            if f.exists():
                targets.append(str(f))
        
        # Deduplicate while preserving order
        seen = set()
        unique_targets = []
        for t in targets:
            if t not in seen:
                seen.add(t)
                unique_targets.append(t)
        
        return unique_targets
    
    def _find_files_containing(self, text: str, limit: int = 10, search_root: Optional[Path] = None) -> List[str]:
        """Find Python files containing specific text in a given root (case-insensitive)."""
        root = search_root or self.saraphina_root
        matches: List[str] = []
        
        # If text looks like a regex pattern, also search using lowercase literal "ultra"
        literals = [text]
        try:
            if text.lower() != text:
                literals.append(text.lower())
        except Exception:
            pass
        
        for py_file in root.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                content_lower = content.lower()
                if any(lit.lower() in content_lower for lit in literals):
                    matches.append(str(py_file))
                    if len(matches) >= limit:
                        break
            except Exception:
                continue
        
        return matches
    
    def _assess_priority(self, user_lower: str) -> str:
        """Assess priority from request"""
        if any(keyword in user_lower for keyword in ['urgent', 'critical', 'immediately', 'asap']):
            return 'critical'
        elif any(keyword in user_lower for keyword in ['important', 'priority', 'soon']):
            return 'high'
        elif any(keyword in user_lower for keyword in ['later', 'eventually', 'minor']):
            return 'low'
        return 'normal'
    
    def create_plan(self, request: ModificationRequest) -> ModificationPlan:
        """
        Create a complete modification plan from request.
        
        Args:
            request: ModificationRequest
        
        Returns:
            ModificationPlan with all details
        """
        logger.info(f"Creating plan for: {request.description}")
        
        patches = []
        spec = None
        validation_results = {}
        
        if request.intent == 'replace_string':
            # Use CodeUpgrader with optional regex replacement
            old_value = request.parameters.get('old_value', '')
            new_value = request.parameters.get('new_value', '')
            use_regex = bool(request.parameters.get('regex', False))
            
            for target in request.targets:
                try:
                    patch = self.upgrader.create_search_replace_patch(
                        target,
                        old_value,
                        new_value,
                        description=f"Replace '{old_value}' with '{new_value}'",
                        regex=use_regex
                    )
                    patches.append(patch)
                except Exception as e:
                    logger.error(f"Failed to create patch for {target}: {e}")
        
        elif request.intent == 'bulk_replace_branding':
            # Build a safe branding map (string-literal oriented)
            branding_map = [
                { 'old': 'Saraphina Ultra - Mission Control', 'new': 'Saraphina - Mission Control' },
                { 'old': 'Saraphina Ultra', 'new': 'Saraphina' },
                { 'old': 'SARAPHINA ULTRA', 'new': 'SARAPHINA' },
                { 'old': 'SARAPHINA ULTRA AI TERMINAL', 'new': 'SARAPHINA AI TERMINAL' },
                { 'old': 'ULTRA AI TERMINAL', 'new': 'AI TERMINAL' },
                { 'old': 'Ultra AI Terminal', 'new': 'AI Terminal' },
                { 'old': 'Ultra', 'new': '' },  # Appears in pure branding strings; identifiers are lowercase
                { 'old': 'ULTRA', 'new': '' },  # Only affects uppercase branding strings
            ]
            # Scan all .py files in repo (project root and package)
            project_root = self.saraphina_root.parent
            py_files = list(project_root.rglob('*.py'))
            # Construct patches per file where at least one mapping matches
            for f in py_files:
                try:
                    content = f.read_text(encoding='utf-8')
                    mods = []
                    for m in branding_map:
                        if m['old'] in content:
                            mods.append({'old': m['old'], 'new': m['new']})
                    if mods:
                        patch = self.upgrader.create_patch_from_modifications(
                            str(f),
                            modifications=mods,
                            description='Global branding cleanup (remove Ultra)'
                        )
                        patches.append(patch)
                except Exception as e:
                    logger.debug(f"Skipping {f}: {e}")
        
        elif request.intent == 'create_module':
            # Use ModuleCreator
            module_name = request.parameters.get('module_name', 'new_module')
            description = request.parameters.get('description', '')
            
            spec = self.creator.create_from_description(description)
            generated = self.creator.create_module(spec)
            
            # Create patches for new files
            from saraphina.code_upgrader import UpgradePatch
            patch = UpgradePatch(
                file_path=generated.module_file,
                old_content='',
                new_content=generated.module_content,
                unified_diff='',
                description=f"Create new module: {module_name}"
            )
            patches.append(patch)
        
        # Assess risk
        risk = self._assess_risk(request, patches)
        
        return ModificationPlan(
            request=request,
            spec=spec,
            patches=patches,
            validation_results=validation_results,
            estimated_risk=risk
        )
    
    def _assess_risk(self, request: ModificationRequest, patches: List[Any]) -> str:
        """Assess risk level of modifications"""
        
        # Critical system files
        critical_files = ['__init__.py', 'main.py', 'saraphina.py']
        
        # Check if modifying critical files
        for patch in patches:
            if hasattr(patch, 'file_path'):
                filename = Path(patch.file_path).name
                if filename in critical_files:
                    return 'high'
        
        # Bulk operations: medium by default unless extremely large
        if request.intent == 'bulk_replace_branding':
            return 'medium' if len(patches) <= 250 else 'high'
        
        # Check number of files
        if len(patches) > 5:
            return 'medium'
        
        # Check if creating new files
        if request.intent == 'create_module':
            return 'low'
        
        # Simple string replacements are low risk
        if request.intent == 'replace_string':
            return 'low'
        
        return 'medium'
    
    def execute_plan(
        self,
        plan: ModificationPlan,
        dry_run: bool = False,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a modification plan.
        
        Args:
            plan: ModificationPlan to execute
            dry_run: If True, don't actually modify files
            auto_approve: If True, skip user confirmation
        
        Returns:
            Dict with execution results
        """
        logger.info(f"Executing plan: {plan.request.description}")
        
        results = {
            'success': False,
            'patches_applied': [],
            'patches_failed': [],
            'backup_paths': [],
            'errors': []
        }
        
        # Set dry run mode
        self.upgrader.dry_run = dry_run
        
        # Validate all patches first
        for patch in plan.patches:
            is_valid, issues = self.upgrader.validate_patch(patch)
            
            if not is_valid:
                results['errors'].append(f"Validation failed for {patch.file_path}: {issues}")
                logger.error(f"Patch validation failed: {issues}")
        
        if results['errors'] and not auto_approve:
            logger.warning("Validation errors found, aborting")
            return results
        
        # Apply patches atomically
        patch_results = self.upgrader.apply_patch_list(
            plan.patches,
            atomic=True
        )
        
        # Collect results
        for file_path, result in patch_results.items():
            if result.success:
                results['patches_applied'].append(file_path)
                if result.backup_path:
                    results['backup_paths'].append(result.backup_path)
            else:
                results['patches_failed'].append(file_path)
                results['errors'].extend(result.errors)
        
        # Overall success
        results['success'] = len(results['patches_failed']) == 0
        
        # Log to learning journal if available
        if results['success'] and self.learning_journal:
            try:
                self._log_to_journal(plan, results)
            except Exception as e:
                logger.warning(f"Failed to log to journal: {e}")
        
        # Git commit if successful and available
        if results['success'] and self.git and self.git.enabled:
            try:
                self._commit_to_git(plan, results)
            except Exception as e:
                logger.warning(f"Failed to commit to git: {e}")
        
        return results
    
    def _log_to_journal(self, plan: ModificationPlan, results: Dict[str, Any]):
        """Log successful modification to learning journal"""
        # TODO: Implement learning journal logging
        logger.info("Logged to learning journal")
    
    def _commit_to_git(self, plan: ModificationPlan, results: Dict[str, Any]):
        """Commit changes to git"""
        files_changed = results['patches_applied']
        
        commit_result = self.git.commit_upgrade(
            artifact_id=f"coord_{plan.request.intent}",
            files_changed=files_changed,
            description=plan.request.description[:100],
            success=True
        )
        
        logger.info(f"Git commit: {commit_result.get('commit_hash', 'unknown')}")
    
    def process_request(
        self,
        user_input: str,
        auto_approve: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Complete end-to-end processing: request → plan → execute.
        
        Args:
            user_input: Natural language request
            auto_approve: Skip confirmation
            dry_run: Don't actually modify files
        
        Returns:
            Dict with complete results
        """
        # Step 1: Parse request
        request = self.parse_request(user_input)
        logger.info(f"Parsed request: {request.intent}")
        
        # Step 2: Create plan
        plan = self.create_plan(request)
        logger.info(f"Created plan with {len(plan.patches)} patches")
        
        # Step 3: Execute plan
        results = self.execute_plan(plan, dry_run=dry_run, auto_approve=auto_approve)
        
        # Add plan info to results
        results['request'] = request.to_dict()
        results['plan'] = plan.to_dict()
        
        return results
    
    def generate_preview(self, plan: ModificationPlan) -> str:
        """
        Generate human-readable preview of planned changes.
        
        Args:
            plan: ModificationPlan
        
        Returns:
            Formatted preview string
        """
        lines = [
            "=" * 60,
            "MODIFICATION PLAN PREVIEW",
            "=" * 60,
            "",
            f"Request: {plan.request.description}",
            f"Intent: {plan.request.intent}",
            f"Priority: {plan.request.priority}",
            f"Risk: {plan.estimated_risk}",
            "",
            f"Files to modify: {len(plan.patches)}",
            ""
        ]
        
        for i, patch in enumerate(plan.patches, 1):
            lines.append(f"{i}. {Path(patch.file_path).name}")
            lines.append(f"   Description: {patch.description}")
            if hasattr(patch, 'unified_diff') and patch.unified_diff:
                # Show first few lines of diff
                diff_lines = patch.unified_diff.splitlines()[:10]
                for diff_line in diff_lines:
                    lines.append(f"   {diff_line}")
                if len(patch.unified_diff.splitlines()) > 10:
                    lines.append(f"   ... ({len(patch.unified_diff.splitlines()) - 10} more lines)")
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)


# CLI interface
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    coordinator = SelfModificationCoordinator()
    
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
        
        print(f"\n📝 Processing request: {user_input}")
        print("")
        
        # Parse request
        request = coordinator.parse_request(user_input)
        print(f"Intent: {request.intent}")
        print(f"Targets: {request.targets}")
        print(f"Parameters: {request.parameters}")
        print("")
        
        # Create plan
        plan = coordinator.create_plan(request)
        
        # Show preview
        preview = coordinator.generate_preview(plan)
        print(preview)
        
        # Ask for confirmation
        response = input("\n✓ Execute this plan? (y/n): ")
        if response.lower() == 'y':
            results = coordinator.execute_plan(plan)
            
            print("\n📊 Results:")
            print(f"  Success: {results['success']}")
            print(f"  Patches applied: {len(results['patches_applied'])}")
            print(f"  Patches failed: {len(results['patches_failed'])}")
            if results['errors']:
                print(f"  Errors: {results['errors']}")
    
    else:
        print("SelfModificationCoordinator - Complete self-modification orchestration")
        print("\nUsage:")
        print("  python self_modification_coordinator.py <natural language request>")
        print("\nExamples:")
        print('  python self_modification_coordinator.py "remove ULTRA from GUI"')
        print('  python self_modification_coordinator.py "create a planner module"')
        print('  python self_modification_coordinator.py "change title to Saraphina AI"')
