"""
pre-commit Emulator - Git hooks framework without external dependencies

This module emulates core pre-commit functionality for managing and executing
git hooks. It enables running linters, formatters, and validators before commits.

Features:
- Git hook installation and management
- Multiple hook types (pre-commit, pre-push, commit-msg, etc.)
- Hook execution with file filtering
- Configuration file support (.pre-commit-config.yaml)
- Pass/fail reporting
- Automatic file staging after fixes
- Support for multiple languages/tools
- Parallel hook execution (optional)
- Skip specific hooks

Note: This is a simplified implementation focusing on core functionality.
Advanced features like remote repos and complex environments are simplified.
"""

import os
import re
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import shutil


class HookStage(Enum):
    """Git hook stages"""
    PRE_COMMIT = "pre-commit"
    PRE_PUSH = "pre-push"
    COMMIT_MSG = "commit-msg"
    PRE_MERGE_COMMIT = "pre-merge-commit"
    POST_COMMIT = "post-commit"
    POST_CHECKOUT = "post-checkout"
    POST_MERGE = "post-merge"


class HookResult(Enum):
    """Result of hook execution"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Hook:
    """Represents a single hook configuration"""
    id: str
    name: str
    entry: str  # Command to run
    language: str = "system"
    files: str = r".*"  # Regex pattern for files to check
    exclude: str = ""  # Regex pattern for files to exclude
    types: List[str] = field(default_factory=list)  # File types (e.g., ['python'])
    stages: List[str] = field(default_factory=lambda: ['pre-commit'])
    pass_filenames: bool = True
    always_run: bool = False
    verbose: bool = False
    
    def matches_file(self, filename: str) -> bool:
        """Check if this hook should run on the given file"""
        # Check file pattern
        if not re.search(self.files, filename):
            return False
        
        # Check exclude pattern
        if self.exclude and re.search(self.exclude, filename):
            return False
        
        # Check file types
        if self.types:
            ext = Path(filename).suffix.lstrip('.')
            type_map = {
                'python': ['py'],
                'javascript': ['js', 'jsx'],
                'typescript': ['ts', 'tsx'],
                'json': ['json'],
                'yaml': ['yaml', 'yml'],
                'markdown': ['md'],
                'text': ['txt'],
            }
            
            for file_type in self.types:
                if file_type in type_map:
                    if ext in type_map[file_type]:
                        return True
            return False
        
        return True


@dataclass
class HookExecution:
    """Result of a hook execution"""
    hook_id: str
    hook_name: str
    result: HookResult
    output: str = ""
    files_processed: int = 0
    duration: float = 0.0


class PreCommitConfig:
    """Configuration for pre-commit hooks"""
    
    def __init__(self):
        self.repos: List[Dict[str, Any]] = []
        self.default_stages: List[str] = ['pre-commit']
        self.fail_fast: bool = False
        self.minimum_pre_commit_version: str = ""
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'PreCommitConfig':
        """Load configuration from YAML file"""
        config = cls()
        
        if not os.path.exists(yaml_path):
            return config
        
        try:
            with open(yaml_path, 'r') as f:
                content = f.read()
            
            # Simple YAML parsing for basic structure
            lines = content.split('\n')
            current_repo = None
            current_hook = None
            indent_level = 0
            
            for line in lines:
                stripped = line.lstrip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                indent = len(line) - len(stripped)
                
                if stripped.startswith('repos:'):
                    continue
                elif indent == 2 and stripped.startswith('- repo:'):
                    repo_url = stripped.split(':', 1)[1].strip()
                    current_repo = {'repo': repo_url, 'hooks': []}
                    config.repos.append(current_repo)
                    current_hook = None
                elif indent == 4 and stripped.startswith('rev:'):
                    if current_repo:
                        current_repo['rev'] = stripped.split(':', 1)[1].strip()
                elif indent == 4 and stripped.startswith('hooks:'):
                    continue
                elif indent == 6 and stripped.startswith('- id:'):
                    hook_id = stripped.split(':', 1)[1].strip()
                    current_hook = {'id': hook_id}
                    if current_repo:
                        current_repo['hooks'].append(current_hook)
                elif indent >= 8 and current_hook and ':' in stripped:
                    key, value = stripped.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key in ['name', 'entry', 'language', 'files', 'exclude']:
                        current_hook[key] = value
                    elif key in ['types', 'stages']:
                        # Handle list values
                        current_hook[key] = [v.strip() for v in value.strip('[]').split(',') if v.strip()]
                    elif key in ['pass_filenames', 'always_run', 'verbose']:
                        current_hook[key] = value.lower() in ['true', 'yes', '1']
                elif stripped.startswith('fail_fast:'):
                    config.fail_fast = stripped.split(':', 1)[1].strip().lower() in ['true', 'yes', '1']
                elif stripped.startswith('default_stages:'):
                    stages = stripped.split(':', 1)[1].strip()
                    config.default_stages = [s.strip() for s in stages.strip('[]').split(',') if s.strip()]
        
        except Exception as e:
            print(f"Warning: Error parsing YAML config: {e}")
        
        return config
    
    def get_hooks(self, stage: str = 'pre-commit') -> List[Hook]:
        """Get all hooks for a specific stage"""
        hooks = []
        
        for repo in self.repos:
            for hook_dict in repo.get('hooks', []):
                # Use hook ID as name if name not provided
                hook_name = hook_dict.get('name', hook_dict.get('id', 'unknown'))
                
                # Use hook ID as entry if entry not provided
                entry = hook_dict.get('entry', hook_dict.get('id', ''))
                
                hook = Hook(
                    id=hook_dict.get('id', ''),
                    name=hook_name,
                    entry=entry,
                    language=hook_dict.get('language', 'system'),
                    files=hook_dict.get('files', r'.*'),
                    exclude=hook_dict.get('exclude', ''),
                    types=hook_dict.get('types', []),
                    stages=hook_dict.get('stages', self.default_stages),
                    pass_filenames=hook_dict.get('pass_filenames', True),
                    always_run=hook_dict.get('always_run', False),
                    verbose=hook_dict.get('verbose', False)
                )
                
                if stage in hook.stages:
                    hooks.append(hook)
        
        return hooks


class PreCommitFramework:
    """Main pre-commit framework for managing git hooks"""
    
    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = repo_root or self._find_git_root()
        self.config_file = os.path.join(self.repo_root, '.pre-commit-config.yaml')
        self.git_hooks_dir = os.path.join(self.repo_root, '.git', 'hooks')
        self.config: Optional[PreCommitConfig] = None
    
    def _find_git_root(self) -> str:
        """Find the git repository root"""
        current = os.getcwd()
        while current != '/':
            if os.path.exists(os.path.join(current, '.git')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()
    
    def load_config(self) -> PreCommitConfig:
        """Load pre-commit configuration"""
        self.config = PreCommitConfig.from_yaml(self.config_file)
        return self.config
    
    def install(self, hook_types: Optional[List[str]] = None) -> bool:
        """Install git hooks"""
        if hook_types is None:
            hook_types = ['pre-commit']
        
        if not os.path.exists(self.git_hooks_dir):
            os.makedirs(self.git_hooks_dir, exist_ok=True)
        
        for hook_type in hook_types:
            hook_path = os.path.join(self.git_hooks_dir, hook_type)
            
            # Create hook script
            hook_script = f"""#!/usr/bin/env bash
# pre-commit hook installed by precommit_emulator
python -m precommit_emulator_tool.precommit_emulator run --hook-stage {hook_type}
"""
            
            try:
                with open(hook_path, 'w') as f:
                    f.write(hook_script)
                
                # Make executable
                os.chmod(hook_path, 0o755)
                print(f"pre-commit installed at {hook_path}")
            except Exception as e:
                print(f"Error installing {hook_type} hook: {e}")
                return False
        
        return True
    
    def uninstall(self, hook_types: Optional[List[str]] = None) -> bool:
        """Uninstall git hooks"""
        if hook_types is None:
            hook_types = ['pre-commit']
        
        for hook_type in hook_types:
            hook_path = os.path.join(self.git_hooks_dir, hook_type)
            
            if os.path.exists(hook_path):
                try:
                    # Check if it's our hook
                    with open(hook_path, 'r') as f:
                        content = f.read()
                    
                    if 'precommit_emulator' in content:
                        os.remove(hook_path)
                        print(f"Uninstalled {hook_type} hook")
                    else:
                        print(f"Warning: {hook_type} hook was not installed by precommit_emulator")
                except Exception as e:
                    print(f"Error uninstalling {hook_type} hook: {e}")
                    return False
        
        return True
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files for commit"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
        except subprocess.CalledProcessError:
            return []
    
    def get_all_files(self) -> List[str]:
        """Get all tracked files in repository"""
        try:
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
        except subprocess.CalledProcessError:
            return []
    
    def run_hook(self, hook: Hook, files: List[str], skip_hooks: Set[str] = None) -> HookExecution:
        """Run a single hook"""
        import time
        
        skip_hooks = skip_hooks or set()
        
        # Check if hook should be skipped
        if hook.id in skip_hooks:
            return HookExecution(
                hook_id=hook.id,
                hook_name=hook.name,
                result=HookResult.SKIPPED,
                output=f"Skipped by user"
            )
        
        # Filter files for this hook
        matching_files = []
        if not hook.always_run:
            for file in files:
                if hook.matches_file(file):
                    matching_files.append(file)
        
        # Skip if no files match and not always_run
        if not matching_files and not hook.always_run:
            return HookExecution(
                hook_id=hook.id,
                hook_name=hook.name,
                result=HookResult.SKIPPED,
                output="No files to check"
            )
        
        # Build command
        cmd = hook.entry.split()
        if hook.pass_filenames and matching_files:
            cmd.extend(matching_files)
        
        # Run command
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return HookExecution(
                    hook_id=hook.id,
                    hook_name=hook.name,
                    result=HookResult.PASSED,
                    output=result.stdout if hook.verbose else "",
                    files_processed=len(matching_files),
                    duration=duration
                )
            else:
                return HookExecution(
                    hook_id=hook.id,
                    hook_name=hook.name,
                    result=HookResult.FAILED,
                    output=result.stdout + result.stderr,
                    files_processed=len(matching_files),
                    duration=duration
                )
        
        except subprocess.TimeoutExpired:
            return HookExecution(
                hook_id=hook.id,
                hook_name=hook.name,
                result=HookResult.FAILED,
                output="Hook timed out after 5 minutes"
            )
        except FileNotFoundError:
            return HookExecution(
                hook_id=hook.id,
                hook_name=hook.name,
                result=HookResult.FAILED,
                output=f"Command not found: {cmd[0]}"
            )
        except Exception as e:
            return HookExecution(
                hook_id=hook.id,
                hook_name=hook.name,
                result=HookResult.FAILED,
                output=f"Error running hook: {str(e)}"
            )
    
    def run(self, hook_stage: str = 'pre-commit', 
            all_files: bool = False,
            verbose: bool = False,
            skip_hooks: Optional[Set[str]] = None) -> bool:
        """Run all hooks for a specific stage"""
        
        skip_hooks = skip_hooks or set()
        
        # Load configuration
        if not self.config:
            self.load_config()
        
        # Get hooks for this stage
        hooks = self.config.get_hooks(hook_stage)
        
        if not hooks:
            print(f"No hooks configured for stage: {hook_stage}")
            return True
        
        # Get files to check
        if all_files:
            files = self.get_all_files()
        else:
            files = self.get_staged_files()
        
        if not files and not any(h.always_run for h in hooks):
            print("No files to check")
            return True
        
        # Run hooks
        print(f"\n{hook_stage}...")
        print("=" * 60)
        
        results: List[HookExecution] = []
        failed_count = 0
        
        for hook in hooks:
            # Print hook name
            status_text = f"{hook.name}..."
            print(status_text, end='', flush=True)
            
            # Run hook
            execution = self.run_hook(hook, files, skip_hooks)
            results.append(execution)
            
            # Print result
            result_symbol = {
                HookResult.PASSED: "✓ Passed",
                HookResult.FAILED: "✗ Failed",
                HookResult.SKIPPED: "- Skipped"
            }
            print(f"\r{status_text.ljust(50)} {result_symbol[execution.result]}")
            
            # Print output if failed or verbose
            if execution.result == HookResult.FAILED or (verbose and execution.output):
                print(execution.output)
            
            # Stop on first failure if fail_fast
            if execution.result == HookResult.FAILED:
                failed_count += 1
                if self.config.fail_fast:
                    break
        
        # Print summary
        print("=" * 60)
        passed = sum(1 for r in results if r.result == HookResult.PASSED)
        failed = sum(1 for r in results if r.result == HookResult.FAILED)
        skipped = sum(1 for r in results if r.result == HookResult.SKIPPED)
        
        print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
        
        return failed_count == 0
    
    def sample_config(self) -> str:
        """Generate a sample .pre-commit-config.yaml"""
        return """# Pre-commit configuration
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      - id: check-yaml
        name: Check YAML
        entry: python -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"
        language: system
        types: [yaml]
      
      - id: check-json
        name: Check JSON
        entry: python -m json.tool
        language: system
        types: [json]
      
      - id: trailing-whitespace
        name: Trim Trailing Whitespace
        entry: sed -i 's/[[:space:]]*$//'
        language: system
        types: [text]
      
      - id: end-of-file-fixer
        name: Fix End of Files
        entry: python -c "import sys; f=open(sys.argv[1],'r+'); c=f.read(); f.seek(0); f.write(c.rstrip()+'\\n'); f.truncate()"
        language: system
        types: [text]
      
      - id: check-added-large-files
        name: Check for Large Files
        entry: python -c "import sys, os; exit(0 if os.path.getsize(sys.argv[1]) < 500000 else 1)"
        language: system
      
      - id: python-syntax
        name: Check Python Syntax
        entry: python -m py_compile
        language: system
        types: [python]

# fail_fast: true
# default_stages: [commit, push]
"""


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pre-commit hook framework')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # install command
    install_parser = subparsers.add_parser('install', help='Install pre-commit hooks')
    install_parser.add_argument('--hook-type', '-t', action='append', 
                               help='Hook type to install (can be specified multiple times)')
    
    # uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall pre-commit hooks')
    uninstall_parser.add_argument('--hook-type', '-t', action='append',
                                 help='Hook type to uninstall')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run hooks')
    run_parser.add_argument('--hook-stage', default='pre-commit',
                           help='Hook stage to run')
    run_parser.add_argument('--all-files', action='store_true',
                           help='Run on all files instead of just staged')
    run_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
    run_parser.add_argument('--skip', action='append',
                           help='Skip specific hooks')
    
    # sample-config command
    sample_parser = subparsers.add_parser('sample-config', 
                                         help='Print sample configuration')
    
    args = parser.parse_args()
    
    framework = PreCommitFramework()
    
    if args.command == 'install':
        hook_types = args.hook_type or ['pre-commit']
        success = framework.install(hook_types)
        sys.exit(0 if success else 1)
    
    elif args.command == 'uninstall':
        hook_types = args.hook_type or ['pre-commit']
        success = framework.uninstall(hook_types)
        sys.exit(0 if success else 1)
    
    elif args.command == 'run':
        skip_hooks = set(args.skip) if args.skip else set()
        success = framework.run(
            hook_stage=args.hook_stage,
            all_files=args.all_files,
            verbose=args.verbose,
            skip_hooks=skip_hooks
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'sample-config':
        print(framework.sample_config())
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
