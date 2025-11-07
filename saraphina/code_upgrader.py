#!/usr/bin/env python3
"""
CodeUpgrader - Safely apply diffs to existing files

Features:
- Unified diff application
- Pre-validation before applying
- Atomic operations with rollback
- Conflict detection
- Integration with backup system
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import difflib
import re
import logging
import shutil

logger = logging.getLogger(__name__)


@dataclass
class UpgradePatch:
    """Represents a patch to apply to a file"""
    file_path: str
    old_content: str
    new_content: str
    unified_diff: str
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'description': self.description,
            'lines_added': self.new_content.count('\n') - self.old_content.count('\n'),
            'diff_preview': '\n'.join(self.unified_diff.splitlines()[:20])
        }


@dataclass
class UpgradeResult:
    """Result of applying an upgrade"""
    success: bool
    file_path: str
    backup_path: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'file_path': self.file_path,
            'backup_path': self.backup_path,
            'errors': self.errors,
            'warnings': self.warnings
        }


class CodeUpgrader:
    """Safely upgrade existing code files"""
    
    def __init__(self, saraphina_root: str = "D:\\Saraphina Root\\saraphina"):
        self.saraphina_root = Path(saraphina_root)
        self.dry_run = False  # If True, don't actually write files
    
    def create_patch(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        description: str = ""
    ) -> UpgradePatch:
        """
        Create an upgrade patch from old and new content.
        
        Args:
            file_path: Path to file to upgrade
            old_content: Current file content
            new_content: Desired file content
            description: Description of the change
        
        Returns:
            UpgradePatch object
        """
        # Generate unified diff
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{Path(file_path).name}",
            tofile=f"b/{Path(file_path).name}",
            lineterm=''
        )
        unified_diff = '\n'.join(diff)
        
        return UpgradePatch(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            unified_diff=unified_diff,
            description=description
        )
    
    def create_patch_from_modifications(
        self,
        file_path: str,
        modifications: List[Dict[str, Any]],
        description: str = ""
    ) -> UpgradePatch:
        """
        Create a patch from a list of modifications.
        
        Args:
            file_path: Path to file
            modifications: List of {old: str, new: str} replacements
            description: Description of changes
        
        Returns:
            UpgradePatch object
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        old_content = path.read_text(encoding='utf-8')
        new_content = old_content
        
        # Apply each modification
        for mod in modifications:
            old_text = mod.get('old', '')
            new_text = mod.get('new', '')
            
            if old_text in new_content:
                new_content = new_content.replace(old_text, new_text, 1)
            else:
                logger.warning(f"Pattern not found in {file_path}: {old_text[:50]}")
        
        return self.create_patch(file_path, old_content, new_content, description)
    
    def validate_patch(self, patch: UpgradePatch) -> Tuple[bool, List[str]]:
        """
        Validate that a patch can be safely applied.
        
        Args:
            patch: UpgradePatch to validate
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check that file exists
        path = Path(patch.file_path)
        if not path.exists():
            issues.append(f"File not found: {patch.file_path}")
            return False, issues
        
        # Check that current content matches expected old content
        current_content = path.read_text(encoding='utf-8')
        if current_content != patch.old_content:
            # Content has changed since patch was created
            similarity = difflib.SequenceMatcher(
                None,
                current_content,
                patch.old_content
            ).ratio()
            
            if similarity < 0.8:
                issues.append(f"File content has changed significantly (similarity: {similarity:.0%})")
                issues.append("Current file may have been modified since patch creation")
            else:
                issues.append(f"Minor differences detected (similarity: {similarity:.0%})")
        
        # Validate Python syntax of new content
        if patch.file_path.endswith('.py'):
            try:
                compile(patch.new_content, patch.file_path, 'exec')
            except SyntaxError as e:
                issues.append(f"Syntax error in new code: {e}")
        
        # Check for common issues
        if 'import' in patch.new_content and 'import' not in patch.old_content:
            issues.append("Warning: New imports added - verify dependencies")
        
        is_valid = len([i for i in issues if not i.startswith('Warning')]) == 0
        return is_valid, issues
    
    def apply_patch(
        self,
        patch: UpgradePatch,
        validate: bool = True,
        create_backup: bool = True
    ) -> UpgradeResult:
        """
        Apply a patch to a file.
        
        Args:
            patch: UpgradePatch to apply
            validate: Whether to validate before applying
            create_backup: Whether to create backup
        
        Returns:
            UpgradeResult with outcome
        """
        logger.info(f"Applying patch to {patch.file_path}")
        
        result = UpgradeResult(
            success=False,
            file_path=patch.file_path
        )
        
        # Validate if requested
        if validate:
            is_valid, issues = self.validate_patch(patch)
            
            # Separate errors and warnings
            for issue in issues:
                if issue.startswith('Warning'):
                    result.warnings.append(issue)
                else:
                    result.errors.append(issue)
            
            if not is_valid:
                logger.error(f"Patch validation failed: {issues}")
                return result
        
        # Create backup if requested
        path = Path(patch.file_path)
        backup_path = None
        
        if create_backup and path.exists():
            backup_path = path.with_suffix(path.suffix + '.pre_upgrade')
            shutil.copy2(path, backup_path)
            result.backup_path = str(backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Apply the patch
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would write {len(patch.new_content)} bytes to {path}")
                result.success = True
            else:
                path.write_text(patch.new_content, encoding='utf-8')
                logger.info(f"Successfully applied patch to {path}")
                result.success = True
        
        except Exception as e:
            result.errors.append(f"Failed to write file: {e}")
            logger.error(f"Failed to apply patch: {e}")
            
            # Restore from backup if available
            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, path)
                    logger.info(f"Restored from backup: {backup_path}")
                    result.errors.append("File restored from backup")
                except Exception as restore_error:
                    result.errors.append(f"Failed to restore backup: {restore_error}")
        
        return result
    
    def apply_patch_list(
        self,
        patches: List[UpgradePatch],
        atomic: bool = True
    ) -> Dict[str, UpgradeResult]:
        """
        Apply multiple patches.
        
        Args:
            patches: List of UpgradePatch objects
            atomic: If True, rollback all if any fails
        
        Returns:
            Dict mapping file paths to UpgradeResult
        """
        results = {}
        applied_patches = []
        
        for patch in patches:
            result = self.apply_patch(patch)
            results[patch.file_path] = result
            
            if result.success:
                applied_patches.append(patch)
            elif atomic:
                # Rollback all previously applied patches
                logger.error(f"Patch failed, rolling back {len(applied_patches)} patches")
                self._rollback_patches(applied_patches)
                break
        
        return results
    
    def _rollback_patches(self, patches: List[UpgradePatch]):
        """Rollback applied patches"""
        for patch in reversed(patches):
            path = Path(patch.file_path)
            backup_path = path.with_suffix(path.suffix + '.pre_upgrade')
            
            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, path)
                    logger.info(f"Rolled back: {path}")
                except Exception as e:
                    logger.error(f"Failed to rollback {path}: {e}")
    
    def generate_upgrade_report(
        self,
        patches: List[UpgradePatch],
        results: Dict[str, UpgradeResult]
    ) -> str:
        """
        Generate a human-readable report of upgrades.
        
        Args:
            patches: List of patches that were applied
            results: Results from apply_patch_list
        
        Returns:
            Formatted report as string
        """
        lines = [
            "=" * 60,
            "UPGRADE REPORT",
            "=" * 60,
            ""
        ]
        
        total = len(patches)
        successful = sum(1 for r in results.values() if r.success)
        failed = total - successful
        
        lines.extend([
            f"Total patches: {total}",
            f"Successful: {successful}",
            f"Failed: {failed}",
            ""
        ])
        
        # Details for each file
        for patch in patches:
            result = results.get(patch.file_path)
            if not result:
                continue
            
            status = "✓ SUCCESS" if result.success else "✗ FAILED"
            lines.append(f"{status} - {Path(patch.file_path).name}")
            
            if patch.description:
                lines.append(f"  Description: {patch.description}")
            
            if result.backup_path:
                lines.append(f"  Backup: {result.backup_path}")
            
            if result.warnings:
                for warning in result.warnings:
                    lines.append(f"  ⚠️  {warning}")
            
            if result.errors:
                for error in result.errors:
                    lines.append(f"  ❌ {error}")
            
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def create_search_replace_patch(
        self,
        file_path: str,
        search: str,
        replace: str,
        description: str = "",
        regex: bool = False
    ) -> UpgradePatch:
        """
        Create a patch for simple search and replace.
        
        Args:
            file_path: File to modify
            search: Text to search for
            replace: Replacement text
            description: Description of change
            regex: Whether search is a regex pattern
        
        Returns:
            UpgradePatch object
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        old_content = path.read_text(encoding='utf-8')
        
        if regex:
            new_content = re.sub(search, replace, old_content)
        else:
            new_content = old_content.replace(search, replace)
        
        if old_content == new_content:
            logger.warning(f"No changes made to {file_path} - pattern not found")
        
        return self.create_patch(
            file_path,
            old_content,
            new_content,
            description or f"Replace '{search[:30]}' with '{replace[:30]}'"
        )
    
    def create_line_insertion_patch(
        self,
        file_path: str,
        after_line: int,
        new_lines: List[str],
        description: str = ""
    ) -> UpgradePatch:
        """
        Create a patch to insert lines after a specific line number.
        
        Args:
            file_path: File to modify
            after_line: Line number to insert after (1-indexed)
            new_lines: Lines to insert
            description: Description of change
        
        Returns:
            UpgradePatch object
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        old_content = path.read_text(encoding='utf-8')
        lines = old_content.splitlines(keepends=True)
        
        # Insert new lines
        insert_idx = after_line  # Convert to 0-indexed
        new_content_lines = lines[:insert_idx] + [line + '\n' for line in new_lines] + lines[insert_idx:]
        new_content = ''.join(new_content_lines)
        
        return self.create_patch(
            file_path,
            old_content,
            new_content,
            description or f"Insert {len(new_lines)} lines after line {after_line}"
        )


# CLI interface
if __name__ == "__main__":
    import sys
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    upgrader = CodeUpgrader()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "search-replace" and len(sys.argv) >= 5:
            file_path = sys.argv[2]
            search = sys.argv[3]
            replace = sys.argv[4]
            
            try:
                patch = upgrader.create_search_replace_patch(
                    file_path,
                    search,
                    replace,
                    description=f"Replace {search} with {replace}"
                )
                
                print("\n📋 Generated Patch:")
                print(patch.unified_diff)
                
                print("\n✓ Validation:")
                is_valid, issues = upgrader.validate_patch(patch)
                print(f"  Valid: {is_valid}")
                if issues:
                    for issue in issues:
                        print(f"    - {issue}")
                
                # Ask for confirmation
                response = input("\n Apply patch? (y/n): ")
                if response.lower() == 'y':
                    result = upgrader.apply_patch(patch)
                    print(f"\n  Result: {'SUCCESS' if result.success else 'FAILED'}")
                    if result.backup_path:
                        print(f"  Backup: {result.backup_path}")
            
            except Exception as e:
                print(f"Error: {e}")
        
        else:
            print("Usage:")
            print("  python code_upgrader.py search-replace <file> <search> <replace>")
    
    else:
        print("CodeUpgrader - Safely apply code modifications")
        print("\nUsage:")
        print("  python code_upgrader.py search-replace <file> <search> <replace>")
