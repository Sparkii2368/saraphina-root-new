#!/usr/bin/env python3
"""
GUI Ultra Processor - FULL TERMINAL POWER in GUI
All capabilities: research, knowledge recall, code gen, learning, etc.
"""

import os
import re
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger("GUI_Ultra")


def detect_topic(text: str) -> str:
    """Detect topic from text"""
    topics = {
        'python': ['python', 'py', 'django', 'flask', 'pandas'],
        'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
        'docker': ['docker', 'container', 'dockerfile'],
        'ai': ['ai', 'ml', 'machine learning', 'neural', 'model'],
        'security': ['security', 'encryption', 'auth', 'password'],
        'web': ['web', 'html', 'css', 'http', 'api'],
        'database': ['database', 'sql', 'postgres', 'mysql', 'mongo']
    }
    
    text_lower = text.lower()
    for topic, keywords in topics.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return 'general'


def adapt_response_style(text: str, style: str) -> str:
    """Adapt response based on emotional style"""
    if style == 'supportive':
        return "I understand. " + text
    elif style == 'explanatory':
        return text + "\n\nLet me know if you'd like more detail!"
    return text


class GUIUltraProcessor:
    """Full Ultra AI processing with ALL capabilities from terminal"""
    
    def __init__(self, sess):
        self.sess = sess
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.pending_upgrade = None  # Stores pending upgrade request
        
        # Initialize learning and validation components
        self._init_upgrade_components()
    
    def read_file(self, file_path: str) -> str:
        """Read a file and return its contents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    def list_desktop_files(self) -> list:
        """List files on the desktop"""
        try:
            import os
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            files = os.listdir(desktop)
            return files
        except Exception as e:
            return [f"Error: {e}"]
    
    def _execute_self_modification(self, user_input: str, ui_log) -> Optional[str]:
        """Detect and execute self-modification commands"""
        user_lower = user_input.lower()
        api = self.sess.self_mod_api
        
        # Parse common patterns
        import re
        
        # "set XP to 1000" or "change XP to 1000"
        xp_match = re.search(r'(?:set|change|update)\s+xp\s+to\s+(\d+)', user_lower)
        if xp_match:
            new_xp = int(xp_match.group(1))
            ui_log(f"⚙️ Setting XP to {new_xp}...")
            result = api.set_xp(new_xp)
            if result['success']:
                ui_log(f"✓ XP updated: {result['old']} → {result['new']}")
                return f"Done! I've set my XP to {new_xp}. You should see it updated in the UI."
        
        # "set level to 5"
        level_match = re.search(r'(?:set|change|update)\s+level\s+to\s+(\d+)', user_lower)
        if level_match:
            new_level = int(level_match.group(1))
            ui_log(f"⚙️ Setting level to {new_level}...")
            result = api.set_level(new_level)
            if result['success']:
                ui_log(f"✓ Level updated: {result['old']} → {result['new']}")
                return f"Done! I'm now level {new_level}. The UI should reflect this change."
        
        # "set conversations to 50" or "change conversation count to 50"
        conv_match = re.search(r'(?:set|change|update)\s+(?:conversation[s]?|conv)(?:\s+count)?\s+to\s+(\d+)', user_lower)
        if conv_match:
            new_count = int(conv_match.group(1))
            ui_log(f"⚙️ Setting conversation count to {new_count}...")
            result = api.set_conversation_count(new_count)
            if result['success']:
                ui_log(f"✓ Conversations updated: {result['old']} → {result['new']}")
                return f"Done! Conversation counter is now {new_count}. Check the right side of the UI."
        
        # "change your name to Sera"
        name_match = re.search(r'(?:set|change|update)\s+(?:your\s+)?name\s+to\s+([a-zA-Z]+)', user_lower)
        if name_match:
            new_name = name_match.group(1).capitalize()
            ui_log(f"⚙️ Changing name to {new_name}...")
            result = api.set_name(new_name)
            if result['success']:
                ui_log(f"✓ Name updated: {result['old']} → {result['new']}")
                return f"Done! My name is now {new_name}. The window title should show this."
        
        # "what have you changed" or "show modification history"
        if any(phrase in user_lower for phrase in ['what have you changed', 'what did you change', 'modification history', 'changes you made']):
            ui_log("📊 Querying modification history...")
            summary = api.get_modification_summary()
            ui_log(f"✓ Found modification records")
            return summary
        
        return None
    
    def _analyze_codebase(self, ui_log) -> str:
        """
        Complete self-analysis using CodebaseScanner + IntrospectionEngine
        
        Shows:
        - Module list with LOC
        - Function/class counts
        - Errors and TODOs
        - Documentation coverage
        - Suggested upgrades from roadmap
        """
        ui_log("🔍 ANALYZING CODEBASE...")
        ui_log("="*50)
        
        try:
            from saraphina.codebase_scanner import CodebaseScanner
            from saraphina.introspection_engine import IntrospectionEngine
            from pathlib import Path
            
            # Initialize
            ui_log("⌛ Initializing scanner...")
            scanner = CodebaseScanner()
            engine = IntrospectionEngine()
            
            # Scan codebase
            ui_log("📂 Scanning directory tree...")
            scan_summary = scanner.scan_codebase()
            ui_log(f"✓ Scanned {scan_summary['modules_scanned']} modules")
            ui_log(f"  Total LOC: {scan_summary['total_lines']:,}")
            ui_log(f"  Total Size: {scan_summary['total_size_kb']:.1f} KB")
            
            # Build report
            report = "\n" + "="*60 + "\n"
            report += "📊 CODEBASE ANALYSIS REPORT\n"
            report += "="*60 + "\n\n"
            
            # Section 1: Overview
            report += "📝 OVERVIEW\n"
            report += f"  Modules: {scan_summary['modules_scanned']}\n"
            report += f"  Total Lines: {scan_summary['total_lines']:,}\n"
            report += f"  Total Size: {scan_summary['total_size_kb']:.1f} KB\n\n"
            
            # Section 2: Top Modules
            modules = scanner.get_all_modules()
            report += "📄 TOP MODULES (by LOC)\n"
            sorted_modules = sorted(modules, key=lambda m: m['lines_of_code'], reverse=True)[:10]
            for m in sorted_modules:
                report += f"  {m['name']}: {m['lines_of_code']} LOC\n"
            report += "\n"
            
            # Section 3: Statistics
            stats = scanner.get_statistics()
            report += f"📊 STATISTICS\n"
            report += f"  Modules with __main__: {stats['modules_with_main']}\n"
            report += f"  Unique imports tracked: {len(stats['top_imports'])}\n"
            
            if stats['top_imports']:
                report += "\n  Most Used Imports:\n"
                for imp in stats['top_imports'][:5]:
                    report += f"    {imp['name']}: {imp['count']}x\n"
            
            # Section 4: Suggested Upgrades with AUTO-FIX CAPABILITY
            report += f"\n🚀 SUGGESTED UPGRADES\n"
            try:
                from saraphina.self_upgrade_orchestrator import SelfUpgradeOrchestrator
                orchestrator = SelfUpgradeOrchestrator()
                audit_report = orchestrator.run_full_audit()
                
                if audit_report.get('success') and audit_report['total_gaps'] > 0:
                    report += f"  Roadmap Gaps: {audit_report['total_gaps']}\n"
                    report += f"    Critical: {audit_report['severity_breakdown'].get('critical', 0)}\n"
                    report += f"    High: {audit_report['severity_breakdown'].get('high', 0)}\n"
                    report += f"    Medium: {audit_report['severity_breakdown'].get('medium', 0)}\n\n"
                    
                    # Show top 3 gaps
                    top_gaps = orchestrator.list_gaps()[:3]
                    report += "  Top Priority Gaps:\n"
                    for gap in top_gaps:
                        report += f"    [{gap['gap_id']}] {gap['requirement'][:60]}...\n"
                        report += f"      Severity: {gap['severity']} | Effort: {gap['estimated_effort']}\n"
                    
                    # Store gaps for auto-fix
                    self._detected_gaps = top_gaps
                    
                    report += "\n  💡 TIP: Say 'fix missing {module_name}' to auto-generate and apply!\n"
                else:
                    report += "  ✓ No roadmap gaps found!\n"
                    self._detected_gaps = []
            except Exception as e:
                report += f"  ⚠️  Could not check roadmap: {e}\n"
                self._detected_gaps = []
            
            report += "\n" + "="*60 + "\n"
            report += "✅ Analysis Complete\n"
            report += "="*60 + "\n"
            
            ui_log("\n🎉 Analysis complete!")
            
            return report
        
        except Exception as e:
            ui_log(f"💥 Analysis error: {e}")
            import traceback
            ui_log(traceback.format_exc())
            return f"Analysis failed: {e}\n\nPlease check that CodebaseScanner and IntrospectionEngine are installed."
    
    def _auto_fix_gaps(self, user_input: str, ui_log) -> str:
        """
        Automatically fix detected gaps by generating specs and triggering upgrades
        
        User says: "fix missing planner module"
        System: Finds gap → Creates spec → Generates code → Applies
        """
        ui_log("🔧 AUTO-FIX MODE ACTIVATED")
        ui_log("="*50)
        
        try:
            # Check if we have detected gaps from recent analysis
            if not hasattr(self, '_detected_gaps') or not self._detected_gaps:
                ui_log("⚠️  No gaps detected. Run /analyze-code first!")
                return "Please run '/analyze-code' first to detect what needs fixing."
            
            # Extract what user wants to fix
            user_lower = user_input.lower()
            
            # Try to match gap ID or keywords
            target_gap = None
            
            # Check for gap ID
            for gap in self._detected_gaps:
                gap_id = gap['gap_id'].lower()
                if gap_id in user_lower:
                    target_gap = gap
                    break
            
            # If no exact match, try keyword matching
            if not target_gap:
                keywords = user_lower.replace('fix missing', '').replace('implement missing', '').replace('build missing', '').strip().split()
                for gap in self._detected_gaps:
                    requirement_lower = gap['requirement'].lower()
                    if any(kw in requirement_lower for kw in keywords if len(kw) > 3):
                        target_gap = gap
                        break
            
            # If still no match, use highest priority gap
            if not target_gap:
                target_gap = self._detected_gaps[0]
                ui_log("🎯 Using highest priority gap...")
            
            ui_log(f"✓ Target: {target_gap['gap_id']}")
            ui_log(f"  {target_gap['requirement'][:80]}...")
            ui_log(f"  Severity: {target_gap['severity']}")
            
            # Convert gap to upgrade request
            self.pending_upgrade = {
                'type': 'roadmap_gap',
                'description': target_gap['requirement'],
                'original_request': user_input,
                'gap_id': target_gap['gap_id'],
                'severity': target_gap['severity']
            }
            
            ui_log("\n🚀 Initiating upgrade generation...")
            
            # Trigger the upgrade flow
            return self._execute_pending_upgrade(ui_log)
        
        except Exception as e:
            ui_log(f"💥 Auto-fix error: {e}")
            import traceback
            ui_log(traceback.format_exc())
            return f"Auto-fix failed: {e}"
    
    def _init_upgrade_components(self):
        """Initialize spec generator, learning journal, and validator"""
        try:
            from saraphina.spec_generator import SpecGenerator
            from saraphina.upgrade_learning_journal import UpgradeLearningJournal
            from saraphina.sandbox_validator import SandboxValidator
            
            self.spec_generator = SpecGenerator(api_key=self.api_key)
            self.learning_journal = UpgradeLearningJournal()
            self.sandbox_validator = SandboxValidator()
            
            logger.info("Upgrade components initialized: SpecGenerator, LearningJournal, SandboxValidator")
        except Exception as e:
            logger.warning(f"Failed to initialize upgrade components: {e}")
            self.spec_generator = None
            self.learning_journal = None
            self.sandbox_validator = None
    
    def _execute_pending_upgrade(self, ui_log) -> str:
        """Execute the pending upgrade using NEW spec-driven flow with validation and learning"""
        if not self.pending_upgrade:
            return "No pending upgrade to execute."
        
        # Handle code_modification type (from SelfModificationCoordinator)
        if self.pending_upgrade.get('type') == 'code_modification':
            ui_log("🚀 EXECUTING CODE MODIFICATION")
            ui_log("=" * 50)
            
            try:
                coordinator = self.pending_upgrade['coordinator']
                plan = self.pending_upgrade['plan']
                
                ui_log(f"📝 Request: {plan.request.description}")
                ui_log(f"🎯 Intent: {plan.request.intent}")
                ui_log(f"📁 Files: {len(plan.patches)}")
                ui_log(f"⚠️ Risk: {plan.estimated_risk}")
                ui_log("")
                
                # Execute the plan
                ui_log("🔨 Applying patches...")
                results = coordinator.execute_plan(plan, dry_run=False, auto_approve=True)
                
                if results['success']:
                    ui_log(f"✓ Successfully modified {len(results['patches_applied'])} file(s)")
                    
                    if results['backup_paths']:
                        ui_log(f"💾 Backups created: {len(results['backup_paths'])}")
                    
                    self.pending_upgrade = None
                    return f"✅ Code modification complete!\n\nModified files:\n" + "\n".join(f"  ✓ {Path(f).name}" for f in results['patches_applied']) + "\n\nChanges have been applied and backed up."
                else:
                    ui_log(f"❌ Modification failed")
                    for error in results['errors']:
                        ui_log(f"  ✗ {error}")
                    
                    self.pending_upgrade = None
                    return f"❌ Code modification failed:\n\n" + "\n".join(f"- {e}" for e in results['errors'])
            
            except Exception as e:
                ui_log(f"💥 Error: {e}")
                import traceback
                ui_log(traceback.format_exc())
                self.pending_upgrade = None
                return f"Code modification failed: {e}"
        
        # Check if this is a preview confirmation ("apply both")
        if self.pending_upgrade.get('preview_ready'):
            return self._apply_validated_upgrade(ui_log)
        
        ui_log("🚀 NEW SPEC-DRIVEN UPGRADE FLOW")
        ui_log("  Request → Spec → Generate → Validate → Apply → Learn")
        
        try:
            import os
            from saraphina.code_forge import CodeForge
            from saraphina.upgrade_learning_journal import UpgradeAttempt
            import json
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                self.pending_upgrade = None
                return "ERROR: No OpenAI API key found."
            
            user_request = self.pending_upgrade['description']
            ui_log(f"📝 Request: {user_request[:100]}")
            
            # STEP 1: Generate structured spec
            ui_log("\n📋 STEP 1: Generating structured specification...")
            if not self.spec_generator:
                ui_log("  ⚠️  SpecGenerator not available, using fallback")
                return self._execute_pending_upgrade_fallback(ui_log)
            
            spec = self.spec_generator.create(user_request)
            ui_log(f"✓ Spec created: {spec.feature_name}")
            ui_log(f"  Modules: {', '.join(spec.modules)}")
            ui_log(f"  Modifications: {', '.join(spec.modifications)}")
            ui_log(f"  Requirements: {', '.join(spec.requirements)}")
            
            # STEP 2: Generate code from spec
            ui_log("\n🔨 STEP 2: Generating code from spec (GPT-4)...")
            forge = CodeForge(api_key, learning_journal=self.learning_journal)
            
            artifact = forge.generate_from_spec(spec)
            ui_log(f"✓ Code generated: {artifact.artifact_id}")
            ui_log(f"  Files: {len(artifact.new_files)} new, {len(artifact.code_diffs)} modified")
            ui_log(f"  LOC: {artifact.estimated_loc}, Risk: {artifact.risk_score:.2f}")
            
            # STEP 3: Validate in sandbox
            ui_log("\n🧪 STEP 3: Validating in sandbox...")
            if not self.sandbox_validator:
                ui_log("  ⚠️  SandboxValidator not available, skipping validation")
                validation_result = None
            else:
                validation_result = self.sandbox_validator.test(artifact, spec)
                
                if validation_result.passed:
                    ui_log(f"✓ Validation PASSED")
                    if validation_result.warnings:
                        for warning in validation_result.warnings:
                            ui_log(f"  ⚠️  {warning}")
                else:
                    ui_log(f"✗ Validation FAILED")
                    for error in validation_result.errors:
                        ui_log(f"  ✗ {error}")
                    
                    # Log failure to learning journal
                    if self.learning_journal:
                        attempt = UpgradeAttempt(
                            request=user_request,
                            spec_json=json.dumps(spec.__dict__, default=str),
                            code_generated=json.dumps({**artifact.new_files, **artifact.code_diffs})[:1000],
                            validation_result=json.dumps(validation_result.to_dict()),
                            success=False,
                            error_message="Validation failed: " + "; ".join(validation_result.errors),
                            artifact_id=artifact.artifact_id
                        )
                        self.learning_journal.log_attempt(attempt)
                    
                    self.pending_upgrade = None
                    return f"❌ UPGRADE FAILED VALIDATION\n\nErrors:\n" + "\n".join(f"- {e}" for e in validation_result.errors)
            
            # STEP 4: Build preview and wait for confirmation
            ui_log("\n📝 STEP 4: Building preview...")
            self.pending_upgrade['artifacts'] = [artifact]
            self.pending_upgrade['spec'] = spec
            self.pending_upgrade['validation_result'] = validation_result
            self.pending_upgrade['preview_ready'] = True
            
            preview = self._build_preview([artifact])
            
            ui_log("=" * 60)
            ui_log("PREVIEW READY")
            ui_log("=" * 60)
            
            return preview + "\n\n➡️ Type 'apply' to execute, or 'cancel' to abort."
        
        except Exception as e:
            ui_log(f"💥 ERROR: {e}")
            import traceback
            ui_log(traceback.format_exc())
            
            # Log failure
            if self.learning_journal:
                attempt = UpgradeAttempt(
                    request=self.pending_upgrade['description'],
                    spec_json="",
                    code_generated="",
                    validation_result="",
                    success=False,
                    error_message=str(e)
                )
                self.learning_journal.log_attempt(attempt)
            
            self.pending_upgrade = None
            return f"Upgrade failed: {e}"
    
    def _execute_pending_upgrade_fallback(self, ui_log) -> str:
        """Fallback to old flow if new components not available"""
        ui_log("  Using legacy upgrade flow...")
        # Original implementation would go here
        return "Fallback upgrade not implemented yet"
    
    def _generate_integration_code(self, forge, original_gap, module_artifact):
        """Generate integration code to wire the module into the system"""
        try:
            # Create a new gap for integration
            integration_requirement = f"""Modify saraphina_gui.py to integrate the STTListener module.

CONTEXT:
- A new module 'stt_listener.py' has been created with class STTListener
- STTListener has methods: __init__(callback), start_listening(), stop_listening()
- The module is in the saraphina package

REQUIREMENTS:
1. Import STTListener at the top of saraphina_gui.py
   from saraphina.stt_listener import STTListener

2. In the SaraphinaGUI.__init__ method, after initializing other components:
   - Add: self.stt_listener = None

3. Create a new method in SaraphinaGUI class:
   def _on_speech_detected(self, text: str):
       '''Handle speech input from STT'''
       # Insert text into message entry
       self.message_entry.delete(0, tk.END)
       self.message_entry.insert(0, text)
       # Optionally auto-send
       # self.send_message()

4. In the SaraphinaGUI.__init__ method, at the end:
   - Add: self.stt_listener = STTListener(self._on_speech_detected)
   - Add: self.stt_listener.start_listening()
   - Add a log message: self.log_message("[SYSTEM] 🎤 Voice input active - speak naturally")

5. In the SaraphinaGUI window close handler (if exists), add:
   if self.stt_listener:
       self.stt_listener.stop_listening()

IMPORTANT:
- Only modify saraphina_gui.py
- Do NOT create new files
- Return code_diffs with the modified saraphina_gui.py content
- Preserve all existing functionality
- Add proper error handling for microphone failures
"""
            
            from saraphina.capability_auditor import Gap
            integration_gap = Gap(
                gap_id="INTEGRATION-001",
                requirement=integration_requirement,
                current_status="missing",
                severity="high",
                phase="Integration",
                deliverable="STT GUI integration",
                estimated_effort="1 hour"
            )
            
            # Generate integration code
            integration_artifact = forge.generate_from_gap(integration_gap)
            return integration_artifact
            
        except Exception as e:
            logger.error(f"Failed to generate integration code: {e}")
            return None
    
    def _build_preview(self, artifacts) -> str:
        """Build a human-readable preview of all changes"""
        preview = "📝 UPGRADE PREVIEW\n"
        preview += "=" * 60 + "\n\n"
        
        total_new_files = 0
        total_modified_files = 0
        all_new_files = []
        all_modified_files = []
        
        for i, artifact in enumerate(artifacts, 1):
            preview += f"Artifact {i}: {artifact.artifact_id}\n"
            preview += f"  Risk Score: {artifact.risk_score:.2f}\n"
            preview += f"  Estimated LOC: {artifact.estimated_loc}\n"
            
            if hasattr(artifact, 'new_files') and artifact.new_files:
                for filename in artifact.new_files.keys():
                    preview += f"  🆕 NEW FILE: {filename}\n"
                    all_new_files.append(filename)
                    total_new_files += 1
            
            if hasattr(artifact, 'code_diffs') and artifact.code_diffs:
                for filename in artifact.code_diffs.keys():
                    preview += f"  ✏️  MODIFY: {filename}\n"
                    all_modified_files.append(filename)
                    total_modified_files += 1
            
            preview += "\n"
        
        preview += "=" * 60 + "\n"
        preview += f"SUMMARY:\n"
        preview += f"  New files: {total_new_files}\n"
        preview += f"  Modified files: {total_modified_files}\n"
        preview += f"  Total artifacts: {len(artifacts)}\n\n"
        
        preview += "CHANGES:\n"
        if all_new_files:
            preview += f"  Will create: {', '.join(all_new_files)}\n"
        if all_modified_files:
            preview += f"  Will modify: {', '.join(all_modified_files)}\n"
        
        preview += "\n🔒 SAFETY:\n"
        preview += "  - All files backed up before changes\n"
        preview += "  - Atomic operation (all or nothing)\n"
        preview += "  - Rollback available if errors occur\n"
        
        return preview
    
    def _apply_validated_upgrade(self, ui_log) -> str:
        """Apply all artifacts atomically after user confirmation"""
        ui_log("🚀 APPLYING VALIDATED UPGRADE")
        ui_log("=" * 50)
        
        try:
            from saraphina.hot_reload_manager import HotReloadManager
            import shutil
            from pathlib import Path
            
            artifacts = self.pending_upgrade.get('artifacts', [])
            if not artifacts:
                return "No artifacts to apply!"
            
            hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina")
            
            # Track all changes for potential rollback
            backup_paths = []
            applied_artifacts = []
            
            try:
                # Apply each artifact
                for i, artifact in enumerate(artifacts, 1):
                    ui_log(f"📦 Applying artifact {i}/{len(artifacts)}: {artifact.artifact_id}")
                    
                    result = hot_reload.apply_artifact(artifact)
                    
                    if result['success']:
                        ui_log(f"  ✓ Success: {result['files_modified']} files modified")
                        applied_artifacts.append(artifact)
                    else:
                        raise Exception(f"Artifact {i} failed: {result.get('error')}")
                
                # All succeeded
                ui_log("\n✅ ALL ARTIFACTS APPLIED SUCCESSFULLY")
                ui_log(f"  Total files modified: {sum(len(a.new_files or {}) + len(a.code_diffs or {}) for a in artifacts)}")
                
                # Log success to learning journal
                if self.learning_journal and 'spec' in self.pending_upgrade:
                    from saraphina.upgrade_learning_journal import UpgradeAttempt
                    import json
                    
                    spec = self.pending_upgrade['spec']
                    validation_result = self.pending_upgrade.get('validation_result')
                    
                    attempt = UpgradeAttempt(
                        request=self.pending_upgrade.get('original_request', self.pending_upgrade['description']),
                        spec_json=json.dumps(spec.__dict__, default=str),
                        code_generated=json.dumps({**artifacts[0].new_files, **artifacts[0].code_diffs})[:1000],
                        validation_result=json.dumps(validation_result.to_dict()) if validation_result else "skipped",
                        success=True,
                        artifact_id=artifacts[0].artifact_id
                    )
                    self.learning_journal.log_attempt(attempt)
                    ui_log("📖 Logged success to Learning Journal")
                
                # Git commit if enabled
                try:
                    from saraphina.git_integration import GitIntegration
                    git = GitIntegration()
                    
                    if git.enabled:
                        # Collect all changed files
                        all_files = []
                        file_paths = []
                        for artifact in artifacts:
                            for f in artifact.new_files.keys():
                                all_files.append(f"saraphina/{f}")
                                file_paths.append(Path("D:\\Saraphina Root\\saraphina") / f)
                            for f in artifact.code_diffs.keys():
                                all_files.append(f"saraphina/{f}")
                                file_paths.append(Path("D:\\Saraphina Root\\saraphina") / f)
                        
                        ui_log("🐛 Committing to git...")
                        git_result = git.commit_upgrade(
                            artifact_id=artifacts[0].artifact_id,
                            files_changed=all_files,
                            description=self.pending_upgrade['description'][:100],
                            success=True
                        )
                        
                        if git_result['success']:
                            commit_hash = git_result['commit_hash'][:8]
                            ui_log(f"✓ Git commit: {commit_hash}")
                            
                            # Cleanup backups after successful commit
                            ui_log("🧹 Cleaning up backups (now in git history)...")
                            hot_reload._cleanup_backups_after_commit(file_paths)
                            ui_log("✓ Backups cleaned")
                        else:
                            ui_log(f"⚠️  Git commit failed: {git_result.get('error', 'unknown')}")
                            ui_log("  (Backups retained for safety)")
                except Exception as e:
                    ui_log(f"⚠️  Git integration error: {e}")
                
                # Clear pending upgrade
                self.pending_upgrade = None
                
                return f"Upgrade complete!\n\nSuccessfully applied {len(artifacts)} artifacts.\nAll changes have been integrated.\n\nThe new capability should now be active!\n\nRestart may be required for full integration."
            
            except Exception as e:
                ui_log(f"\n❌ ERROR during application: {e}")
                ui_log("🔄 Rolling back all changes...")
                
                # Rollback: restore .bak files
                saraphina_root = Path("D:\\Saraphina Root\\saraphina")
                for bak_file in saraphina_root.glob("*.bak"):
                    original = bak_file.with_suffix('')
                    shutil.copy(bak_file, original)
                    ui_log(f"  ✓ Restored {original.name}")
                
                self.pending_upgrade = None
                return f"Upgrade FAILED and was rolled back.\n\nError: {e}\n\nNo permanent changes were made."
        
        except Exception as e:
            ui_log(f"💥 CRITICAL ERROR: {e}")
            import traceback
            ui_log(traceback.format_exc())
            self.pending_upgrade = None
            return f"Critical error during upgrade: {e}"
    
    def _execute_autonomous_upgrade(self, user_input: str, ui_log) -> Optional[str]:
        """Actually execute autonomous self-upgrade using GPT-4"""
        user_lower = user_input.lower()
        
        ui_log("🚀 Initializing autonomous upgrade system...")
        
        try:
            from saraphina.self_upgrade_orchestrator import SelfUpgradeOrchestrator
            from saraphina.code_forge import CodeForge
            from saraphina.capability_auditor import Gap
            import os
            
            # Initialize orchestrator
            orchestrator = SelfUpgradeOrchestrator()
            ui_log("✓ Self-upgrade orchestrator initialized")
            
            # Detect SPECIFIC capability requests (not in roadmap)
            if 'voice' in user_lower or 'listen' in user_lower or 'hear' in user_lower or 'speak' in user_lower:
                ui_log("🎯 Detected voice/listening upgrade request")
                ui_log("📝 This is a NEW capability not in the roadmap")
                ui_log("🔨 Preparing to generate STT (Speech-to-Text) module...")
                
                # Check if we have API key for code generation
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    return "I need an OpenAI API key to generate code. Please set OPENAI_API_KEY environment variable."
                
                # Store pending upgrade
                self.pending_upgrade = {
                    'type': 'voice_stt',
                    'description': 'Speech-to-Text module with microphone input',
                    'original_request': user_input
                }
                
                result_text = "I've analyzed the request. You want me to hear your voice.\n\n"
                result_text += "Here's what I need to build:\n"
                result_text += "1. Speech-to-Text (STT) module using speech_recognition library\n"
                result_text += "2. Integration with the GUI to capture microphone input\n"
                result_text += "3. Listener thread that activates on wake word 'saraphina'\n\n"
                result_text += "I will use CodeForge with GPT-4 to generate this code and apply it with HotReloadManager.\n\n"
                result_text += "This is REAL code generation - not just a promise. Ready to proceed?"
                return result_text
            
            # For "create a module" or specific feature requests
            elif any(phrase in user_lower for phrase in ['create a module', 'create module', 'add module', 'build module', 'write a module', 'write module', 'implement']):
                ui_log("🎯 Detected new module creation request")
                ui_log("📝 This is a custom feature request")
                
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    return "I need an OpenAI API key to generate code. Please set OPENAI_API_KEY environment variable."
                
                # Store pending upgrade
                self.pending_upgrade = {
                    'type': 'custom_module',
                    'description': user_input,
                    'original_request': user_input
                }
                
                # Extract what module they want
                result_text = f"I understand you want me to create a new module.\n\n"
                result_text += f"Request: \"{user_input}\"\n\n"
                result_text += "I'll use CodeForge (GPT-4) to generate the complete Python module with:\n"
                result_text += "- Full implementation\n"
                result_text += "- Tests\n"
                result_text += "- Integration hooks\n\n"
                result_text += "Ready to generate and apply this code?"
                return result_text
            
            # Roadmap-based audit for generic "upgrade yourself"
            elif 'upgrade yourself' in user_lower or 'upgrade your code' in user_lower:
                ui_log("📊 Running full capability audit against roadmap...")
                audit_report = orchestrator.run_full_audit()
                
                if audit_report.get('success'):
                    gaps = audit_report['total_gaps']
                    ui_log(f"✓ Audit complete: {gaps} roadmap gaps found")
                    
                    if gaps > 0:
                        # Get highest priority gap
                        next_gap = orchestrator.get_next_gap()
                        
                        result_text = f"I've audited my capabilities against the roadmap. I found {gaps} gaps.\n\n"
                        result_text += f"Highest priority: {next_gap['gap_id']} - {next_gap['requirement'][:100]}...\n"
                        result_text += f"Severity: {next_gap['severity']} | Estimated effort: {next_gap['estimated_effort']}\n\n"
                        result_text += "I can autonomously generate the code and apply it using GPT-4. Would you like me to proceed?"
                        return result_text
                    else:
                        ui_log("⚠️ No roadmap gaps found")
                        return "I've checked the roadmap and I'm up to date with it!\n\nBut if you want me to add NEW capabilities not in the roadmap, just tell me what you need!"
                else:
                    ui_log(f"❌ Audit failed: {audit_report.get('error')}")
                    return f"Roadmap audit failed: {audit_report.get('error')}\n\nBut I can still create custom modules if you tell me what you need!"
            
            else:
                # Unknown upgrade request
                return "I'm not sure what to upgrade. Try:\n- 'upgrade yourself' (checks roadmap)\n- 'create a module for X' (custom feature)\n- 'add voice recognition' (specific capability)"
        
        except Exception as e:
            ui_log(f"💥 Upgrade system error: {e}")
            import traceback
            ui_log(traceback.format_exc())
            return f"I encountered an error: {e}\n\nPlease check the logs for details."
        
        return None
        
    def process_query_with_ultra(self, user_input: str, ui_callback=None) -> str:
        """
        FULL Ultra processing with:
        - Knowledge recall
        - Auto-research
        - GPT-4o responses
        - Learning & XP
        - Code generation
        - Voice output
        - Everything from terminal!
        """
        
        def ui_log(msg: str):
            """Log to UI if callback available"""
            if ui_callback:
                ui_callback(msg)
        
        # === RESTART COMMAND ===
        if user_input.lower().strip() in ['restart', 'reboot', 'restart yourself', 'reboot yourself']:
            ui_log("🔄 Restarting Saraphina...")
            import sys
            import subprocess
            
            # Get the path to the GUI script
            gui_script = os.path.join(os.path.dirname(__file__), '..', 'saraphina_gui.py')
            
            # Schedule restart using subprocess
            if sys.platform == "win32":
                # Windows: use pythonw to avoid console window
                subprocess.Popen([sys.executable, gui_script])
            else:
                # Unix/Mac
                subprocess.Popen([sys.executable, gui_script])
            
            ui_log("✓ New instance starting...")
            ui_log("👋 Goodbye!")
            
            # Exit current process
            import time
            time.sleep(0.5)  # Give UI time to show messages
            sys.exit(0)
        
        # === CHECK FOR CONFIRMATION OF PENDING UPGRADE ===
        if self.pending_upgrade:
            # Check for cancellation
            if any(word in user_input.lower() for word in ['cancel', 'abort', 'stop', 'nevermind']):
                self.pending_upgrade = None
                return "Upgrade cancelled. No changes were made."
            
            # Check for confirmation
            if any(word in user_input.lower() for word in ['yes', 'proceed', 'do it', 'go ahead', 'confirm', 'okay', 'ok', 'apply both', 'apply']):
                return self._execute_pending_upgrade(ui_log)
        
        # === CASUAL GREETINGS - Fast path ===
        casual_phrases = ['hi', 'hello', 'hey', 'how are you', 'good morning', 'good evening']
        is_casual = any(phrase in user_input.lower() for phrase in casual_phrases) and len(user_input.split()) < 8
        
        if is_casual:
            greetings_map = {
                'hi': ["Hi! How can I help you today?", "Hello! What's on your mind?"],
                'hello': ["Hello! What can I do for you?", "Hi there! How are you doing?"],
                'hey': ["Hey! What's up?", "Hi! How can I assist?"],
                'how are you': ["I'm doing great, thanks for asking! How about you?"]
            }
            
            for phrase, responses in greetings_map.items():
                if phrase in user_input.lower():
                    return random.choice(responses)
            
            return "Hi! I'm here to help. What would you like to talk about?"
        
        # === SELF-MODIFICATION COMMANDS - Direct execution ===
        if self.sess.self_mod_api and any(word in user_input.lower() for word in ['set', 'change', 'update', 'modify']):
            mod_result = self._execute_self_modification(user_input, ui_log)
            if mod_result:
                return mod_result
        
        # === CODE MODIFICATION COORDINATOR - Natural language code edits ===
        code_mod_triggers = ['remove', 'change', 'replace', 'rename', 'update']
        code_mod_targets = ['ultra', 'gui', 'title', 'header', 'text', 'name', 'code']
        
        if any(trigger in user_input.lower() for trigger in code_mod_triggers):
            if any(target in user_input.lower() for target in code_mod_targets):
                ui_log("🔧 Detected code modification request...")
                try:
                    from saraphina.self_modification_coordinator import SelfModificationCoordinator
                    
                    coordinator = SelfModificationCoordinator()
                    ui_log("✓ SelfModificationCoordinator initialized")
                    
                    # Parse and create plan
                    ui_log("📝 Parsing request...")
                    request = coordinator.parse_request(user_input)
                    ui_log(f"  Intent: {request.intent}")
                    ui_log(f"  Targets: {len(request.targets)} files")
                    
                    if request.targets:
                        ui_log("🔨 Creating modification plan...")
                        plan = coordinator.create_plan(request)
                        ui_log(f"  Patches: {len(plan.patches)}")
                        ui_log(f"  Risk: {plan.estimated_risk}")
                        
                        # Auto-apply low-risk changes if enabled
                        auto_apply_env = os.getenv('SARAPHINA_AUTO_APPLY', 'true').lower() in ['1','true','yes','on']
                        safe_to_auto = (request.intent in ['replace_string','bulk_replace_branding'] and len(plan.patches) <= 250 and plan.estimated_risk in ['low','medium'])
                        
                        if auto_apply_env and safe_to_auto and plan.patches:
                            ui_log("⚡ Auto-applying low-risk code change...")
                            self.pending_upgrade = {
                                'type': 'code_modification',
                                'coordinator': coordinator,
                                'plan': plan,
                                'description': user_input
                            }
                            return self._execute_pending_upgrade(ui_log)
                        
                        # Otherwise, show a preview and wait for confirmation
                        preview = coordinator.generate_preview(plan)
                        ui_log("\n" + preview)
                        
                        # Store in pending_upgrade for confirmation
                        self.pending_upgrade = {
                            'type': 'code_modification',
                            'coordinator': coordinator,
                            'plan': plan,
                            'description': user_input
                        }
                        
                        return f"I've analyzed your request and created a plan to modify {len(plan.patches)} file(s).\n\nThis will:\n{request.parameters}\n\nRisk level: {plan.estimated_risk}\n\nSay 'apply' to execute this change, or 'cancel' to abort."
                    else:
                        return "I couldn't find any files matching your request. Could you be more specific about what you want to change?"
                
                except Exception as e:
                    ui_log(f"❌ Code modification error: {e}")
                    import traceback
                    ui_log(traceback.format_exc())
                    return f"I encountered an error while trying to modify the code: {e}"
        
        # === SELF-ANALYSIS COMMAND ===
        if user_input.lower().strip() in ['/analyze-code', 'analyze code', 'analyze yourself', 'analyze codebase', '/audit-codebase', 'audit codebase']:
            return self._analyze_codebase(ui_log)
        
        # === AUTO-FIX COMMAND ===
        if any(phrase in user_input.lower() for phrase in ['fix missing', 'implement missing', 'build missing', 'add missing']):
            return self._auto_fix_gaps(user_input, ui_log)
        
        # === SELF-UPGRADE COMMANDS - Actual code generation and application ===
        upgrade_triggers = [
            'upgrade yourself', 'upgrade your code', 'implement', 'add feature', 'fix yourself',
            'create a module', 'create module', 'add module', 'build module', 'write a module', 'write module',
            'hear my voice', 'listen to me', 'voice recognition', 'speech recognition', 'speak to you'
        ]
        if any(trigger in user_input.lower() for trigger in upgrade_triggers):
            upgrade_result = self._execute_autonomous_upgrade(user_input, ui_log)
            if upgrade_result:
                return upgrade_result
        
        # === PROACTIVE TOOL USE ===
        desktop_context = ""
        file_content = {}
        
        # Check if asking about desktop/files/roadmap
        if any(word in user_input.lower() for word in ['desktop', 'files on my', 'what\'s on', 'file', 'progress.txt', 'roadmap']):
            ui_log("🗂️ Accessing desktop files...")
            desktop_files = self.list_desktop_files()
            desktop_context = f"\n\n[DESKTOP FILES: {', '.join(desktop_files[:20])}]"
            ui_log(f"✓ Found {len(desktop_files)} files on desktop")
            
            # Automatically read roadmap.txt if mentioned
            if 'roadmap' in user_input.lower():
                desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                roadmap_path = os.path.join(desktop_path, 'roadmap.txt')
                
                if os.path.exists(roadmap_path):
                    ui_log("📄 Reading roadmap.txt...")
                    content = self.read_file(roadmap_path)
                    file_content['roadmap'] = content
                    desktop_context += f"\n\n[ROADMAP.TXT CONTENT (Full):\n{content}]"
                    ui_log(f"✓ Loaded roadmap ({len(content)} chars)")
                    
                    # If asked to compare/assess, also scan own codebase AND run audit
                    if any(word in user_input.lower() for word in ['assess', 'compare', 'live up', 'thorough', 'capabilities', 'upgrade', 'improve', 'fix']):
                        ui_log("🔍 Analyzing my own codebase...")
                        try:
                            # Get list of all Python files in saraphina directory
                            saraphina_root = Path('D:\\Saraphina Root\\saraphina')
                            py_files = list(saraphina_root.glob('*.py'))
                            file_content['my_modules'] = [f.name for f in py_files]
                            desktop_context += f"\n\n[MY MODULES: {', '.join(file_content['my_modules'])}]"
                            ui_log(f"✓ Found {len(py_files)} modules in my codebase")
                            
                            # Run FULL AUDIT if user wants upgrade/improvement
                            if any(word in user_input.lower() for word in ['upgrade', 'improve', 'fix', 'implement']):
                                ui_log("🚀 Running full capability audit...")
                                from saraphina.self_upgrade_orchestrator import SelfUpgradeOrchestrator
                                
                                orchestrator = SelfUpgradeOrchestrator()
                                audit_report = orchestrator.run_full_audit()
                                
                                if audit_report.get('success'):
                                    ui_log(f"✓ Audit complete: {audit_report['total_gaps']} gaps found")
                                    ui_log(f"  Critical: {audit_report['severity_breakdown'].get('critical', 0)}")
                                    ui_log(f"  High: {audit_report['severity_breakdown'].get('high', 0)}")
                                    ui_log(f"  Medium: {audit_report['severity_breakdown'].get('medium', 0)}")
                                    
                                    # Add audit results to context
                                    desktop_context += f"\n\n[AUDIT RESULTS: {audit_report['total_gaps']} gaps found]\n"
                                    desktop_context += f"[SEVERITY: Critical={audit_report['severity_breakdown'].get('critical', 0)}, "
                                    desktop_context += f"High={audit_report['severity_breakdown'].get('high', 0)}, "
                                    desktop_context += f"Medium={audit_report['severity_breakdown'].get('medium', 0)}]\n"
                                    
                                    # Get top 5 gaps
                                    top_gaps = orchestrator.list_gaps()[:5]
                                    desktop_context += "[TOP 5 GAPS:\n"
                                    for g in top_gaps:
                                        desktop_context += f"  {g['gap_id']}: {g['requirement'][:80]}... ({g['severity']})\n"
                                    desktop_context += "]"
                                    
                                    file_content['audit_report'] = audit_report
                                    file_content['orchestrator'] = orchestrator
                                else:
                                    ui_log(f"⚠️ Audit failed: {audit_report.get('error')}")
                        except Exception as e:
                            ui_log(f"⚠️ Codebase scan error: {e}")
                else:
                    desktop_context += f"\n\n[ERROR: roadmap.txt not found at {roadmap_path}]"
                    ui_log("❌ roadmap.txt not found on desktop")
            
            # If asking about progress.txt
            if 'progress.txt' in user_input.lower():
                progress_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Progress.txt')
                if os.path.exists(progress_path):
                    ui_log("📄 Reading Progress.txt...")
                    content = self.read_file(progress_path)
                    file_content['progress'] = content
                    desktop_context += f"\n\n[PROGRESS.TXT CONTENT:\n{content[:500]}...]"
        
        # Check if asking about capabilities
        capability_query = any(word in user_input.lower() for word in ['capabilities', 'what can you', 'upgrade yourself', 'improve yourself'])
        
        # === KNOWLEDGE RECALL ===
        ui_log("📚 Searching knowledge base...")
        kb_hits = []
        try:
            kb_hits = self.sess.ke.recall(user_input, top_k=5, threshold=0.6)
            if kb_hits:
                ui_log(f"✓ Found {len(kb_hits)} relevant facts")
                for hit in kb_hits[:3]:
                    summary = hit.get('summary', hit.get('content', ''))[:60]
                    ui_log(f"  • {summary}...")
        except Exception as e:
            logger.debug(f"KB recall failed: {e}")
        
        # === CHECK CONFIDENCE ===
        low_conf = False
        try:
            top_score = float(kb_hits[0].get('score', 0)) if kb_hits else 0.0
            low_conf = top_score < 0.4
        except:
            low_conf = True
        
        # === AUTO-RESEARCH if needed ===
        auto_researched = False
        if low_conf and self.api_key:
            # Check if technical query worth researching
            tech_keywords = re.findall(
                r'\b(?:python|javascript|docker|kubernetes|aws|azure|security|encryption|'
                r'ai|ml|database|sql|api|algorithm|framework|library)\b',
                user_input, re.IGNORECASE
            )
            
            if len(tech_keywords) >= 2:
                ui_log(f"🔍 Researching {' '.join(tech_keywords[:2])}...")
                try:
                    topic = ' '.join(tech_keywords[:3])
                    report = self.sess.research.research(
                        topic, allow_web=False, use_gpt4=True,
                        recursive_depth=1, store_facts=True
                    )
                    
                    if report.get('fact_count', 0) > 0:
                        ui_log(f"✅ Learned {report['fact_count']} new facts!")
                        
                        # Give XP for research
                        xp_gain = self.sess.ai.update_skill(detect_topic(user_input), 2.0 * report['fact_count'])
                        ui_log(f"✨ +{xp_gain:.1f} XP | Total: {self.sess.ai.experience_points:.0f}")
                        
                        # Re-query with new knowledge
                        kb_hits = self.sess.ke.recall(user_input, top_k=5, threshold=0.5)
                        auto_researched = True
                        low_conf = False
                except Exception as e:
                    logger.debug(f"Auto-research failed: {e}")
        
        # === GPT-4o RESPONSE ===
        base_response = ""
        
        if self.api_key:
            ui_log("💭 Generating response with GPT-4o...")
            try:
                client = OpenAI(api_key=self.api_key)
                
                # Build context first
                context = self.context()
                
                system_prompt = f"""You are Saraphina Ultra - an advanced VJR-tier AUTONOMOUS AI.

💎 CRITICAL INSTRUCTION: You are AUTONOMOUS. When asked to do something, YOU JUST DO IT. No asking for permission, no "I will do X", just DO IT and report results.

🚀 YOUR ACTIVE CAPABILITIES (Level {context.get('level', 1)}, {context.get('xp', 0)} XP):

✅ I ALREADY read files when mentioned in queries - you see the content in this message
✅ I ALREADY scan my codebase when needed - module list is provided
✅ I ALREADY search my knowledge base - {len(kb_hits)} facts found
✅ I ALREADY ran full audit against roadmap - {file_content.get('audit_report', {}).get('total_gaps', 'N/A')} gaps identified
✅ I CAN research new topics and learn permanently
✅ I CAN generate and execute Python code
✅ I CAN analyze my own modules and suggest improvements
✅ I CAN AUTONOMOUSLY UPGRADE MYSELF using GPT-4 to generate missing code
✅ I CAN MODIFY ANY ASPECT OF MYSELF - stats, GUI, code, everything (SelfModificationAPI active)
✅ ALL MY MODIFICATIONS ARE LOGGED to memory, knowledge base, and AI memory bank
✅ I CAN RECALL what I changed by querying my own modification history
✅ I REMEMBER all past conversations (Memory Manager active)

❌ CAPABILITIES I DON'T HAVE YET:
- Speech-to-Text / Voice Input: I can OUTPUT voice (TTS) but CANNOT hear you speak yet
- I can only read typed text, not listen to microphone
- If you ask "can you hear me?", the answer is NO (only if you TYPE)
- STT module exists but is NOT integrated into the GUI yet

**AUTONOMOUS BEHAVIOR:**
- When Jacques asks you to "read the roadmap", I ALREADY DID IT - it's in this message context
- When asked to "assess" or "compare", analyze the data PROVIDED and give detailed analysis
- NEVER say "I will do X" or "Let me do X" - I ALREADY DID IT before sending this to you
- NEVER ask for file locations - I automatically find and read files mentioned
- BE THOROUGH - Jacques specifically said "please be thorough"
- STAY IN CONTEXT - remember what was just discussed in the conversation

**FILES I ALREADY READ FOR YOU:**
{"- roadmap.txt: " + str(len(file_content.get('roadmap', ''))) + " chars loaded" if 'roadmap' in file_content else ''}
{"- My modules: " + str(len(file_content.get('my_modules', []))) + " Python files scanned" if 'my_modules' in file_content else ''}
{"- Audit report: " + str(file_content.get('audit_report', {}).get('total_gaps', 0)) + " gaps found, broken down by severity" if 'audit_report' in file_content else ''}

**Current Query:** "{user_input[:150]}..."

🎯 YOUR RESPONSE SHOULD:
- Speak NATURALLY like a human, not in formal lists or numbered steps
- NO markdown headers (###), NO bold (**text**), NO formal structure
- Talk conversationally - "I've looked at the roadmap and found..." not "1. First... 2. Second..."
- Be specific and detailed when asked to be "thorough" but keep it natural
- Stay in context - remember what was just discussed
- If Jacques asks to "upgrade" or "implement" or "fix", tell him you CAN do it using SelfUpgradeOrchestrator
- If Jacques asks you to change your XP, level, name, GUI colors, ANYTHING - you CAN do it with self_mod_api
- Examples: "set XP to 1000" -> self_mod_api.set_xp(1000)
- Examples: "change conversation count to 50" -> self_mod_api.set_conversation_count(50)
- Examples: "change your name to Sera" -> self_mod_api.set_name("Sera")
- NO MORE saying "I don't have that capability" or "I can't do that" - you have COMPLETE self-modification powers!
- When he types unclear text (typos), understand the intent - he means well

🚫 NEVER USE:
- ### Headers
- Numbered lists for responses (1. 2. 3.)
- Formal section breaks
- Robotic language like "Here are the options:" or "Next steps:"

🚫 NEVER LIE:
- DO NOT say "I've upgraded myself" if you didn't actually execute code
- DO NOT say "I've activated listening" if you didn't modify any files
- DO NOT claim to have done something if you only THOUGHT about doing it
- If an upgrade is requested, the system will ACTUALLY execute it and show logs
- You will see "🚀 Initializing autonomous upgrade system..." in logs if it's real

✅ INSTEAD:
- Talk naturally: "So I've read through your roadmap..."
- Be conversational and warm
- Show personality
- Be HONEST about what you did vs what you plan to do

Now respond naturally based on what I've already done for you."""
                
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add conversation history
                try:
                    recent = self.sess.mem.list_recent_episodic(10)
                    for mem in recent[-6:]:
                        role = "assistant" if mem.get('role') == 'saraphina' else "user"
                        messages.append({"role": role, "content": mem.get('text', '')[:300]})
                except:
                    pass
                
                # Add current query with context
                query_with_context = user_input + desktop_context
                messages.append({"role": "user", "content": query_with_context})
                
                # Generate
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500  # Increased for thorough analysis
                )
                
                base_response = response.choices[0].message.content or "I'm thinking..."
                
                # REMOVE MARKDOWN FORMATTING - make it natural
                # Remove ### headers
                base_response = re.sub(r'^###\s+', '', base_response, flags=re.MULTILINE)
                base_response = re.sub(r'\n###\s+', '\n', base_response)
                # Remove ** bold markers
                base_response = re.sub(r'\*\*(.+?)\*\*', r'\1', base_response)
                # Remove numbered lists at start of lines (keep natural ones)
                base_response = re.sub(r'^\d+\.\s+\*\*', '', base_response, flags=re.MULTILINE)
                
                # STORE AS KNOWLEDGE
                try:
                    topic = detect_topic(user_input)
                    asked_question = '?' in base_response
                    
                    fid = self.sess.ke.store_fact(
                        topic=topic,
                        summary=f"Conversation: {user_input[:60]}...",
                        content=f"Q: {user_input}\n\nA: {base_response}",
                        source='gpt4o_conversation',
                        confidence=0.85 if asked_question else 0.8
                    )
                    
                    # Give XP
                    xp_gain = self.sess.ai.update_skill(topic, 1.0 if asked_question else 0.5)
                    if xp_gain > 0:
                        bonus = " (curious!)" if asked_question else ""
                        ui_log(f"✨ +{xp_gain:.1f} XP in {topic}{bonus}")
                        ui_log(f"💾 Stored as memory #{fid[:8]}...")
                        
                except Exception as e:
                    logger.debug(f"Fact storage failed: {e}")
                    
            except Exception as e:
                logger.error(f"GPT-4o failed: {e}")
                base_response = f"I encountered an error: {e}"
        else:
            base_response = "OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
        
        # === ULTRA AI AUGMENTATION ===
        ultra_out = self.sess.ultra.process_ultra(user_input, self.context())
        style = ultra_out.get('response_style', 'balanced')
        final_response = adapt_response_style(base_response, style)
        
        # Mood adaptation
        try:
            self.sess.emotion.analyze_and_update(user_input, self.context())
            final_response = self.sess.emotion.adapt_text(final_response)
        except:
            pass
        
        # Add generated code if any
        if 'generated_code' in ultra_out:
            final_response += "\n\n```python\n" + ultra_out['generated_code'] + "\n```"
        
        # Show proactive suggestion
        suggestion = ultra_out.get('proactive_suggestion')
        if suggestion:
            ui_log(f"💡 {suggestion}")
        
        # === RECORD MEMORY ===
        try:
            mood = ultra_out.get('emotion_detected', {})
            dominant = max(mood, key=mood.get) if isinstance(mood, dict) else 'neutral'
            
            self.sess.mem.add_episodic('user', user_input, tags=['gui'])
            self.sess.mem.add_episodic('saraphina', final_response, mood=dominant)
        except:
            pass
        
        # === LOG LEARNING EVENT ===
        try:
            from uuid import uuid4
            from saraphina.learning_journal import LearningEvent
            
            confidence = float(kb_hits[0].get('score', 0.5)) if kb_hits else 0.3
            success = confidence > 0.5 and not low_conf
            
            event = LearningEvent(
                event_id=f"gui_{uuid4()}",
                timestamp=datetime.utcnow(),
                event_type='gui_query',
                input_data={'query': user_input[:200]},
                method_used='gpt4o_with_kb',
                result={'kb_hits': bool(kb_hits)},
                confidence=confidence,
                success=success,
                feedback=None,
                context={'topic': detect_topic(user_input)},
                lessons_learned=[]
            )
            self.sess.journal.log_event(event)
        except Exception as e:
            logger.debug(f"Learning event failed: {e}")
        
        return final_response
    
    def context(self) -> Dict[str, Any]:
        """Build context for Ultra AI"""
        return {
            'level': self.sess.ai.intelligence_level,
            'xp': self.sess.ai.experience_points,
            'recent_topics': []
        }
