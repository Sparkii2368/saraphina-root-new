#!/usr/bin/env python3
"""
Git Integration - Auto-commit successful upgrades

After each successful upgrade:
1. Stage changed files
2. Commit with artifact ID and description
3. Optionally push to remote
"""
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("GitIntegration")


class GitIntegration:
    """Automatic git commits for successful upgrades"""
    
    def __init__(self, repo_path: str = "D:\\Saraphina Root"):
        self.repo_path = Path(repo_path)
        self.enabled = self._check_git_available()
        
        if self.enabled:
            logger.info(f"Git integration enabled for {self.repo_path}")
        else:
            logger.warning("Git not available or not a git repository")
    
    def _check_git_available(self) -> bool:
        """Check if git is available and this is a git repo"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Git check failed: {e}")
            return False
    
    def commit_upgrade(self, artifact_id: str, files_changed: List[str],
                      description: str, success: bool = True) -> Dict[str, Any]:
        """
        Commit an upgrade to git
        
        Args:
            artifact_id: Unique artifact identifier
            files_changed: List of file paths that changed
            description: Human-readable description
            success: Whether upgrade was successful
        
        Returns:
            Dict with success status and commit hash
        """
        if not self.enabled:
            return {'success': False, 'error': 'Git not enabled'}
        
        try:
            # Stage files
            for file_path in files_changed:
                full_path = self.repo_path / file_path
                if full_path.exists():
                    subprocess.run(
                        ['git', 'add', str(file_path)],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True
                    )
            
            # Build commit message
            status_emoji = "✅" if success else "❌"
            commit_msg = f"{status_emoji} Auto-upgrade: {description}\n\n"
            commit_msg += f"Artifact: {artifact_id}\n"
            commit_msg += f"Timestamp: {datetime.now().isoformat()}\n"
            commit_msg += f"Files changed:\n"
            for file_path in files_changed:
                commit_msg += f"  - {file_path}\n"
            commit_msg += "\n[Automated commit by Saraphina Self-Upgrade System]"
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get commit hash
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            logger.info(f"Committed upgrade {artifact_id}: {commit_hash[:8]}")
            
            return {
                'success': True,
                'commit_hash': commit_hash,
                'files_committed': len(files_changed)
            }
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Git commit failed: {error_msg}")
            return {'success': False, 'error': error_msg}
        
        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return {'success': False, 'error': str(e)}
    
    def push_to_remote(self, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """
        Push commits to remote repository
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: main)
        
        Returns:
            Dict with success status
        """
        if not self.enabled:
            return {'success': False, 'error': 'Git not enabled'}
        
        try:
            result = subprocess.run(
                ['git', 'push', remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Pushed to {remote}/{branch}")
                return {'success': True}
            else:
                error_msg = result.stderr
                logger.warning(f"Push failed: {error_msg}")
                return {'success': False, 'error': error_msg}
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Push timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_recent_commits(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent commits"""
        if not self.enabled:
            return []
        
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%s|%ai'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) == 3:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'date': parts[2]
                    })
            
            return commits
        
        except Exception as e:
            logger.error(f"Failed to get commits: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get git repository status"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            # Get current branch
            branch = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Get status
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout
            
            # Count changes
            lines = [l for l in status.split('\n') if l.strip()]
            modified = len([l for l in lines if l.startswith(' M')])
            added = len([l for l in lines if l.startswith('A')])
            untracked = len([l for l in lines if l.startswith('??')])
            
            return {
                'enabled': True,
                'branch': branch,
                'modified': modified,
                'added': added,
                'untracked': untracked,
                'clean': len(lines) == 0
            }
        
        except Exception as e:
            return {'enabled': True, 'error': str(e)}


# CLI
if __name__ == "__main__":
    import sys
    
    git = GitIntegration()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            status = git.get_status()
            print("\nGit Status:")
            print(f"  Enabled: {status.get('enabled')}")
            if status.get('enabled'):
                print(f"  Branch: {status.get('branch')}")
                print(f"  Modified: {status.get('modified', 0)}")
                print(f"  Added: {status.get('added', 0)}")
                print(f"  Untracked: {status.get('untracked', 0)}")
                print(f"  Clean: {status.get('clean', False)}")
        
        elif command == "recent":
            commits = git.get_recent_commits(5)
            print(f"\n{len(commits)} recent commits:")
            for c in commits:
                print(f"  {c['hash'][:8]} - {c['message'][:60]}")
                print(f"    {c['date']}")
    else:
        print("Usage: python git_integration.py [status|recent]")
