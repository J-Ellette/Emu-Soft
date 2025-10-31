"""
Tests for pre-commit emulator

This test suite validates the pre-commit hook framework functionality.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from GitHooks import (
    Hook, HookResult, HookStage, PreCommitConfig, PreCommitFramework,
    HookExecution
)


class TestHook(unittest.TestCase):
    """Test Hook class"""
    
    def test_hook_creation(self):
        """Test creating a hook"""
        hook = Hook(
            id='test-hook',
            name='Test Hook',
            entry='echo test',
            language='system'
        )
        
        self.assertEqual(hook.id, 'test-hook')
        self.assertEqual(hook.name, 'Test Hook')
        self.assertEqual(hook.entry, 'echo test')
    
    def test_hook_matches_file_basic(self):
        """Test file matching with basic pattern"""
        hook = Hook(
            id='test',
            name='Test',
            entry='test',
            files=r'.*\.py$'
        )
        
        self.assertTrue(hook.matches_file('test.py'))
        self.assertFalse(hook.matches_file('test.js'))
    
    def test_hook_matches_file_with_exclude(self):
        """Test file matching with exclude pattern"""
        hook = Hook(
            id='test',
            name='Test',
            entry='test',
            files=r'.*\.py$',
            exclude=r'test_.*\.py$'
        )
        
        self.assertTrue(hook.matches_file('main.py'))
        self.assertFalse(hook.matches_file('test_main.py'))
    
    def test_hook_matches_file_with_types(self):
        """Test file matching with types"""
        hook = Hook(
            id='test',
            name='Test',
            entry='test',
            types=['python']
        )
        
        self.assertTrue(hook.matches_file('test.py'))
        self.assertFalse(hook.matches_file('test.js'))
    
    def test_hook_default_values(self):
        """Test hook default values"""
        hook = Hook(
            id='test',
            name='Test',
            entry='test'
        )
        
        self.assertEqual(hook.language, 'system')
        self.assertTrue(hook.pass_filenames)
        self.assertFalse(hook.always_run)
        self.assertEqual(hook.stages, ['pre-commit'])


class TestPreCommitConfig(unittest.TestCase):
    """Test PreCommitConfig class"""
    
    def test_config_creation(self):
        """Test creating a config"""
        config = PreCommitConfig()
        
        self.assertEqual(len(config.repos), 0)
        self.assertEqual(config.default_stages, ['pre-commit'])
        self.assertFalse(config.fail_fast)
    
    def test_config_from_yaml(self):
        """Test loading config from YAML"""
        yaml_content = """
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      - id: test-hook
        name: Test Hook
        entry: echo test
        language: system
        types: [python]
        stages: [pre-commit]
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            config = PreCommitConfig.from_yaml(yaml_path)
            
            self.assertEqual(len(config.repos), 1)
            self.assertEqual(config.repos[0]['repo'], 'local')
            self.assertEqual(len(config.repos[0]['hooks']), 1)
            self.assertEqual(config.repos[0]['hooks'][0]['id'], 'test-hook')
        finally:
            os.unlink(yaml_path)
    
    def test_config_get_hooks(self):
        """Test getting hooks for a stage"""
        config = PreCommitConfig()
        config.repos = [
            {
                'repo': 'local',
                'hooks': [
                    {
                        'id': 'hook1',
                        'name': 'Hook 1',
                        'entry': 'echo 1',
                        'stages': ['pre-commit']
                    },
                    {
                        'id': 'hook2',
                        'name': 'Hook 2',
                        'entry': 'echo 2',
                        'stages': ['pre-push']
                    }
                ]
            }
        ]
        
        pre_commit_hooks = config.get_hooks('pre-commit')
        self.assertEqual(len(pre_commit_hooks), 1)
        self.assertEqual(pre_commit_hooks[0].id, 'hook1')
        
        pre_push_hooks = config.get_hooks('pre-push')
        self.assertEqual(len(pre_push_hooks), 1)
        self.assertEqual(pre_push_hooks[0].id, 'hook2')


class TestPreCommitFramework(unittest.TestCase):
    """Test PreCommitFramework class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(self.git_dir)
        
        # Initialize as git repo
        os.makedirs(os.path.join(self.git_dir, 'hooks'), exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_framework_creation(self):
        """Test creating framework"""
        framework = PreCommitFramework(self.test_dir)
        
        self.assertEqual(framework.repo_root, self.test_dir)
        self.assertTrue(framework.config_file.endswith('.pre-commit-config.yaml'))
    
    def test_install_hooks(self):
        """Test installing hooks"""
        framework = PreCommitFramework(self.test_dir)
        
        success = framework.install(['pre-commit'])
        self.assertTrue(success)
        
        hook_path = os.path.join(framework.git_hooks_dir, 'pre-commit')
        self.assertTrue(os.path.exists(hook_path))
        self.assertTrue(os.access(hook_path, os.X_OK))
    
    def test_uninstall_hooks(self):
        """Test uninstalling hooks"""
        framework = PreCommitFramework(self.test_dir)
        
        # Install first
        framework.install(['pre-commit'])
        
        # Then uninstall
        success = framework.uninstall(['pre-commit'])
        self.assertTrue(success)
        
        hook_path = os.path.join(framework.git_hooks_dir, 'pre-commit')
        self.assertFalse(os.path.exists(hook_path))
    
    def test_load_config(self):
        """Test loading configuration"""
        yaml_content = """
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      - id: test-hook
        name: Test Hook
        entry: echo test
"""
        
        config_path = os.path.join(self.test_dir, '.pre-commit-config.yaml')
        with open(config_path, 'w') as f:
            f.write(yaml_content)
        
        framework = PreCommitFramework(self.test_dir)
        config = framework.load_config()
        
        self.assertIsNotNone(config)
        self.assertEqual(len(config.repos), 1)
    
    def test_run_hook_success(self):
        """Test running a successful hook"""
        framework = PreCommitFramework(self.test_dir)
        
        hook = Hook(
            id='test',
            name='Test',
            entry='echo success',
            pass_filenames=False,
            always_run=True  # Need this to run without files
        )
        
        result = framework.run_hook(hook, [])
        
        self.assertEqual(result.result, HookResult.PASSED)
        self.assertEqual(result.hook_id, 'test')
    
    def test_run_hook_failure(self):
        """Test running a failing hook"""
        framework = PreCommitFramework(self.test_dir)
        
        hook = Hook(
            id='test',
            name='Test',
            entry='false',  # This command always fails
            pass_filenames=False,
            always_run=True  # Need this to run without files
        )
        
        result = framework.run_hook(hook, [])
        
        self.assertEqual(result.result, HookResult.FAILED)
    
    def test_run_hook_with_files(self):
        """Test running hook with file filtering"""
        framework = PreCommitFramework(self.test_dir)
        
        # Create test files
        test_py = os.path.join(self.test_dir, 'test.py')
        test_js = os.path.join(self.test_dir, 'test.js')
        
        Path(test_py).touch()
        Path(test_js).touch()
        
        hook = Hook(
            id='test',
            name='Test',
            entry='echo',
            files=r'.*\.py$'
        )
        
        result = framework.run_hook(hook, ['test.py', 'test.js'])
        
        self.assertEqual(result.files_processed, 1)
    
    def test_run_hook_skip(self):
        """Test skipping a hook"""
        framework = PreCommitFramework(self.test_dir)
        
        hook = Hook(
            id='test',
            name='Test',
            entry='echo test'
        )
        
        result = framework.run_hook(hook, [], skip_hooks={'test'})
        
        self.assertEqual(result.result, HookResult.SKIPPED)
    
    def test_sample_config(self):
        """Test generating sample config"""
        framework = PreCommitFramework(self.test_dir)
        
        sample = framework.sample_config()
        
        self.assertIn('repos:', sample)
        self.assertIn('hooks:', sample)
        self.assertIn('check-yaml', sample)


class TestHookExecution(unittest.TestCase):
    """Test HookExecution class"""
    
    def test_execution_creation(self):
        """Test creating execution result"""
        execution = HookExecution(
            hook_id='test',
            hook_name='Test Hook',
            result=HookResult.PASSED,
            output='Success',
            files_processed=5,
            duration=1.5
        )
        
        self.assertEqual(execution.hook_id, 'test')
        self.assertEqual(execution.hook_name, 'Test Hook')
        self.assertEqual(execution.result, HookResult.PASSED)
        self.assertEqual(execution.files_processed, 5)
        self.assertEqual(execution.duration, 1.5)


class TestHookStage(unittest.TestCase):
    """Test HookStage enum"""
    
    def test_hook_stages(self):
        """Test hook stage values"""
        self.assertEqual(HookStage.PRE_COMMIT.value, 'pre-commit')
        self.assertEqual(HookStage.PRE_PUSH.value, 'pre-push')
        self.assertEqual(HookStage.COMMIT_MSG.value, 'commit-msg')


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(self.git_dir)
        os.makedirs(os.path.join(self.git_dir, 'hooks'), exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Test complete workflow"""
        # Create config
        yaml_content = """
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      - id: echo-test
        name: Echo Test
        entry: echo
        language: system
        pass_filenames: false
        always_run: true
"""
        
        config_path = os.path.join(self.test_dir, '.pre-commit-config.yaml')
        with open(config_path, 'w') as f:
            f.write(yaml_content)
        
        # Create framework
        framework = PreCommitFramework(self.test_dir)
        
        # Install hooks
        success = framework.install()
        self.assertTrue(success)
        
        # Load config
        config = framework.load_config()
        self.assertIsNotNone(config)
        
        # Get hooks
        hooks = config.get_hooks('pre-commit')
        self.assertEqual(len(hooks), 1)
        
        # Run hook
        result = framework.run_hook(hooks[0], [])
        self.assertEqual(result.result, HookResult.PASSED)
        
        # Uninstall hooks
        success = framework.uninstall()
        self.assertTrue(success)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
