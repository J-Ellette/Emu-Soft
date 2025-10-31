#!/usr/bin/env python3
"""
Test suite for Jenkins Emulator

Tests core functionality including:
- Job creation and management
- Build execution
- Pipeline execution
- Build status tracking
- Console output capture
"""

import unittest
import time
from IniLogger import (
    IniLogger, Job, Pipeline, BuildStatus, BuildResult,
    TriggerType, create_job, create_pipeline, build_job
)


class TestIniLogger(unittest.TestCase):
    """Test Jenkins emulator basic functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_create_job(self):
        """Test job creation"""
        job = self.jenkins.create_job("test-job", "Test job description")
        
        self.assertIsNotNone(job)
        self.assertEqual(job.name, "test-job")
        self.assertEqual(job.description, "Test job description")
        self.assertTrue(job.enabled)
    
    def test_get_job(self):
        """Test retrieving a job"""
        self.jenkins.create_job("my-job")
        job = self.jenkins.get_job("my-job")
        
        self.assertIsNotNone(job)
        self.assertEqual(job.name, "my-job")
    
    def test_delete_job(self):
        """Test deleting a job"""
        self.jenkins.create_job("temp-job")
        result = self.jenkins.delete_job("temp-job")
        
        self.assertTrue(result)
        self.assertIsNone(self.jenkins.get_job("temp-job"))
    
    def test_list_jobs(self):
        """Test listing all jobs"""
        self.jenkins.create_job("job1")
        self.jenkins.create_job("job2")
        self.jenkins.create_job("job3")
        
        jobs = self.jenkins.list_jobs()
        self.assertEqual(len(jobs), 3)
        self.assertIn("job1", jobs)
        self.assertIn("job2", jobs)
        self.assertIn("job3", jobs)


class TestJobBuild(unittest.TestCase):
    """Test job build functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_build_simple_job(self):
        """Test building a simple job"""
        job = self.jenkins.create_job("build-test")
        build = self.jenkins.build_job("build-test", wait=True)
        
        self.assertIsNotNone(build)
        self.assertEqual(build.build_number, 1)
        self.assertEqual(build.job_name, "build-test")
        self.assertTrue(build.is_complete())
    
    def test_build_with_script(self):
        """Test building job with custom script"""
        def custom_script(params):
            return True
        
        job = self.jenkins.create_job("script-job", script=custom_script)
        build = self.jenkins.build_job("script-job", wait=True)
        
        self.assertEqual(build.status, BuildStatus.SUCCESS)
    
    def test_build_with_failing_script(self):
        """Test building job with failing script"""
        def failing_script(params):
            return False
        
        job = self.jenkins.create_job("fail-job", script=failing_script)
        build = self.jenkins.build_job("fail-job", wait=True)
        
        self.assertEqual(build.status, BuildStatus.FAILURE)
        self.assertTrue(build.is_failure())
    
    def test_build_with_parameters(self):
        """Test building job with parameters"""
        def param_script(params):
            assert params["version"] == "1.0"
            assert params["branch"] == "main"
            return True
        
        job = self.jenkins.create_job("param-job", script=param_script)
        build = self.jenkins.build_job(
            "param-job",
            parameters={"version": "1.0", "branch": "main"},
            wait=True
        )
        
        self.assertEqual(build.status, BuildStatus.SUCCESS)
        self.assertEqual(build.parameters["version"], "1.0")
    
    def test_multiple_builds(self):
        """Test multiple builds of same job"""
        job = self.jenkins.create_job("multi-build")
        
        build1 = self.jenkins.build_job("multi-build", wait=True)
        build2 = self.jenkins.build_job("multi-build", wait=True)
        build3 = self.jenkins.build_job("multi-build", wait=True)
        
        self.assertEqual(build1.build_number, 1)
        self.assertEqual(build2.build_number, 2)
        self.assertEqual(build3.build_number, 3)
        self.assertEqual(len(job.builds), 3)
    
    def test_get_build_status(self):
        """Test getting build status"""
        job = self.jenkins.create_job("status-job")
        build = self.jenkins.build_job("status-job", wait=True)
        
        status = self.jenkins.get_build_status("status-job", build.build_number)
        self.assertIn(status, [BuildStatus.SUCCESS, BuildStatus.FAILURE])
    
    def test_console_output(self):
        """Test console output capture"""
        job = self.jenkins.create_job("console-job")
        build = self.jenkins.build_job("console-job", wait=True)
        
        output = self.jenkins.get_console_output("console-job", build.build_number)
        self.assertIsInstance(output, list)
        self.assertGreater(len(output), 0)


class TestJobManagement(unittest.TestCase):
    """Test job management features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_get_last_build(self):
        """Test getting last build"""
        job = self.jenkins.create_job("last-build-job")
        
        self.jenkins.build_job("last-build-job", wait=True)
        self.jenkins.build_job("last-build-job", wait=True)
        build3 = self.jenkins.build_job("last-build-job", wait=True)
        
        last_build = job.get_last_build()
        self.assertEqual(last_build.build_number, 3)
    
    def test_get_last_successful_build(self):
        """Test getting last successful build"""
        def alternate_script(params):
            return params.get("succeed", True)
        
        job = self.jenkins.create_job("success-job", script=alternate_script)
        
        self.jenkins.build_job("success-job", {"succeed": True}, wait=True)
        self.jenkins.build_job("success-job", {"succeed": False}, wait=True)
        self.jenkins.build_job("success-job", {"succeed": False}, wait=True)
        
        last_success = job.get_last_successful_build()
        self.assertEqual(last_success.build_number, 1)
    
    def test_disabled_job(self):
        """Test that disabled jobs don't build"""
        job = self.jenkins.create_job("disabled-job")
        job.enabled = False
        
        build = self.jenkins.build_job("disabled-job", wait=True)
        self.assertIsNone(build)


class TestPipeline(unittest.TestCase):
    """Test pipeline functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_create_pipeline(self):
        """Test pipeline creation"""
        pipeline = self.jenkins.create_pipeline("test-pipeline")
        
        self.assertIsNotNone(pipeline)
        self.assertEqual(pipeline.name, "test-pipeline")
    
    def test_pipeline_stages(self):
        """Test adding stages to pipeline"""
        pipeline = self.jenkins.create_pipeline("staged-pipeline")
        
        def build_step(params):
            pass
        
        def test_step(params):
            pass
        
        pipeline.add_stage("Build", [build_step])
        pipeline.add_stage("Test", [test_step])
        
        self.assertEqual(len(pipeline.stages), 2)
        self.assertEqual(pipeline.stages[0]["name"], "Build")
        self.assertEqual(pipeline.stages[1]["name"], "Test")
    
    def test_execute_pipeline(self):
        """Test pipeline execution"""
        pipeline = self.jenkins.create_pipeline("exec-pipeline")
        
        executed_stages = []
        
        def stage1_step(params):
            executed_stages.append("stage1")
        
        def stage2_step(params):
            executed_stages.append("stage2")
        
        pipeline.add_stage("Stage 1", [stage1_step])
        pipeline.add_stage("Stage 2", [stage2_step])
        
        build = self.jenkins.execute_pipeline("exec-pipeline")
        
        self.assertIsNotNone(build)
        self.assertEqual(len(executed_stages), 2)


class TestPlugins(unittest.TestCase):
    """Test plugin management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_install_plugin(self):
        """Test installing a plugin"""
        self.jenkins.install_plugin("git")
        
        plugins = self.jenkins.get_installed_plugins()
        self.assertIn("git", plugins)
    
    def test_multiple_plugins(self):
        """Test installing multiple plugins"""
        self.jenkins.install_plugin("git")
        self.jenkins.install_plugin("docker")
        self.jenkins.install_plugin("kubernetes")
        
        plugins = self.jenkins.get_installed_plugins()
        self.assertEqual(len(plugins), 3)


class TestGlobalConfig(unittest.TestCase):
    """Test global configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.jenkins = IniLogger()
    
    def test_set_config(self):
        """Test setting global config"""
        self.jenkins.set_global_config("master_url", "http://jenkins.local")
        
        url = self.jenkins.get_global_config("master_url")
        self.assertEqual(url, "http://jenkins.local")
    
    def test_config_persistence(self):
        """Test config values persist"""
        self.jenkins.set_global_config("num_executors", 4)
        self.jenkins.set_global_config("admin_email", "admin@example.com")
        
        self.assertEqual(self.jenkins.get_global_config("num_executors"), 4)
        self.assertEqual(self.jenkins.get_global_config("admin_email"), "admin@example.com")


if __name__ == "__main__":
    unittest.main()
