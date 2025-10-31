"""
Tests for Fabric emulator

Comprehensive test suite for SSH deployment automation tool functionality.


Developed by PowerShield
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from Deployment_Engine import (
    Connection, Config, Group, SerialGroup, ThreadingGroup,
    Result, Transfer, task,
    run, sudo, put, get,
    FabricError, ConnectionError, CommandError, TransferError,
    _command_history, _file_transfers, _connections
)


class TestConnection(unittest.TestCase):
    """Test SSH connection functionality."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_connection_creation(self):
        """Test creating a connection."""
        conn = Connection('example.com', user='admin')
        
        self.assertEqual(conn.host, 'example.com')
        self.assertEqual(conn.user, 'admin')
        self.assertEqual(conn.port, 22)
    
    def test_connection_open_close(self):
        """Test opening and closing connection."""
        conn = Connection('example.com')
        
        self.assertFalse(conn.is_connected)
        
        conn.open()
        self.assertTrue(conn.is_connected)
        
        conn.close()
        self.assertFalse(conn.is_connected)
    
    def test_connection_context_manager(self):
        """Test using connection as context manager."""
        with Connection('example.com') as conn:
            self.assertTrue(conn.is_connected)
        
        self.assertFalse(conn.is_connected)


class TestCommandExecution(unittest.TestCase):
    """Test command execution functionality."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_run_command(self):
        """Test running a command."""
        conn = Connection('example.com')
        result = conn.run('echo Hello')
        
        self.assertIsInstance(result, Result)
        self.assertEqual(result.command, 'echo Hello')
        self.assertTrue(result.ok)
        self.assertFalse(result.failed)
    
    def test_run_command_with_output(self):
        """Test command with output."""
        conn = Connection('example.com')
        result = conn.run('echo Hello World')
        
        self.assertEqual(result.stdout, 'Hello World')
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.exited, 0)
    
    def test_sudo_command(self):
        """Test running sudo command."""
        conn = Connection('example.com')
        result = conn.sudo('apt-get update')
        
        self.assertIn('sudo', result.command)
        self.assertTrue(result.ok)
    
    def test_sudo_with_user(self):
        """Test sudo with specific user."""
        conn = Connection('example.com')
        result = conn.sudo('ls /home/user', user='otheruser')
        
        self.assertIn('sudo -u otheruser', result.command)
    
    def test_local_command(self):
        """Test running local command."""
        conn = Connection('example.com')
        result = conn.local('echo Local')
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.ok)
    
    def test_command_history(self):
        """Test that commands are logged."""
        conn = Connection('example.com')
        conn.run('ls')
        conn.run('pwd')
        
        self.assertEqual(len(_command_history), 2)
        self.assertEqual(_command_history[0]['command'], 'ls')
        self.assertEqual(_command_history[1]['command'], 'pwd')


class TestFileTransfer(unittest.TestCase):
    """Test file transfer functionality."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_put_file(self):
        """Test uploading a file."""
        conn = Connection('example.com')
        transfer = conn.put('local.txt', '/remote/path/file.txt')
        
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.local, 'local.txt')
        self.assertEqual(transfer.remote, '/remote/path/file.txt')
        self.assertEqual(transfer.operation, 'put')
        self.assertTrue(transfer.success)
    
    def test_get_file(self):
        """Test downloading a file."""
        conn = Connection('example.com')
        transfer = conn.get('/remote/file.txt', 'local.txt')
        
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.remote, '/remote/file.txt')
        self.assertEqual(transfer.local, 'local.txt')
        self.assertEqual(transfer.operation, 'get')
        self.assertTrue(transfer.success)
    
    def test_put_without_remote_path(self):
        """Test put with default remote path."""
        conn = Connection('example.com')
        transfer = conn.put('myfile.txt')
        
        self.assertEqual(transfer.local, 'myfile.txt')
        self.assertEqual(transfer.remote, 'myfile.txt')
    
    def test_file_transfer_history(self):
        """Test that transfers are logged."""
        conn = Connection('example.com')
        conn.put('file1.txt', '/remote/file1.txt')
        conn.get('/remote/file2.txt', 'file2.txt')
        
        self.assertEqual(len(_file_transfers), 2)
        self.assertEqual(_file_transfers[0]['transfer'].operation, 'put')
        self.assertEqual(_file_transfers[1]['transfer'].operation, 'get')


class TestResult(unittest.TestCase):
    """Test Result object."""
    
    def test_result_success(self):
        """Test successful result."""
        result = Result(command='ls', stdout='file.txt', exited=0)
        
        self.assertTrue(result.ok)
        self.assertFalse(result.failed)
        self.assertTrue(bool(result))
        self.assertEqual(str(result), 'file.txt')
    
    def test_result_failure(self):
        """Test failed result."""
        result = Result(command='false', stderr='error', exited=1)
        
        self.assertFalse(result.ok)
        self.assertTrue(result.failed)
        self.assertFalse(bool(result))


class TestConfig(unittest.TestCase):
    """Test configuration functionality."""
    
    def test_config_creation(self):
        """Test creating configuration."""
        config = Config()
        
        self.assertIsInstance(config.run, type(config.run))
        self.assertIsInstance(config.sudo, type(config.sudo))
        self.assertIsInstance(config.timeouts, type(config.timeouts))
    
    def test_config_with_overrides(self):
        """Test config with overrides."""
        config = Config(overrides={'key': 'value'})
        
        self.assertEqual(config.overrides['key'], 'value')
    
    def test_config_clone(self):
        """Test cloning configuration."""
        config1 = Config(overrides={'key': 'value'})
        config2 = config1.clone()
        
        self.assertEqual(config2.overrides['key'], 'value')
        self.assertIsNot(config1, config2)


class TestGroup(unittest.TestCase):
    """Test group functionality."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_group_creation(self):
        """Test creating a group."""
        group = Group('host1.com', 'host2.com', 'host3.com', user='admin')
        
        self.assertEqual(len(group.connections), 3)
        self.assertEqual(group.hosts, ('host1.com', 'host2.com', 'host3.com'))
    
    def test_group_run(self):
        """Test running command on group."""
        group = Group('host1.com', 'host2.com')
        results = group.run('echo test')
        
        self.assertEqual(len(results), 2)
        self.assertIn('host1.com', results)
        self.assertIn('host2.com', results)
        self.assertTrue(results['host1.com'].ok)
        self.assertTrue(results['host2.com'].ok)
    
    def test_group_sudo(self):
        """Test running sudo command on group."""
        group = Group('host1.com', 'host2.com')
        results = group.sudo('apt-get update')
        
        self.assertEqual(len(results), 2)
        for result in results.values():
            self.assertIn('sudo', result.command)
    
    def test_group_put(self):
        """Test uploading file to group."""
        group = Group('host1.com', 'host2.com')
        results = group.put('local.txt', '/remote/file.txt')
        
        self.assertEqual(len(results), 2)
        for transfer in results.values():
            self.assertEqual(transfer.operation, 'put')
            self.assertTrue(transfer.success)
    
    def test_group_close(self):
        """Test closing all connections in group."""
        group = Group('host1.com', 'host2.com')
        for conn in group.connections:
            conn.open()
        
        group.close()
        
        for conn in group.connections:
            self.assertFalse(conn.is_connected)


class TestTaskDecorator(unittest.TestCase):
    """Test task decorator."""
    
    def test_task_decorator(self):
        """Test decorating function as task."""
        @task
        def deploy():
            return "deployed"
        
        self.assertTrue(hasattr(deploy, 'is_task'))
        self.assertTrue(deploy.is_task)
        self.assertEqual(deploy(), "deployed")


class TestModuleFunctions(unittest.TestCase):
    """Test module-level convenience functions."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_run_function(self):
        """Test module-level run function."""
        result = run('ls', 'example.com', user='admin')
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.ok)
    
    def test_sudo_function(self):
        """Test module-level sudo function."""
        result = sudo('apt-get update', 'example.com')
        
        self.assertIn('sudo', result.command)
        self.assertTrue(result.ok)
    
    def test_put_function(self):
        """Test module-level put function."""
        transfer = put('local.txt', '/remote/file.txt', 'example.com')
        
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.operation, 'put')
    
    def test_get_function(self):
        """Test module-level get function."""
        transfer = get('/remote/file.txt', 'local.txt', 'example.com')
        
        self.assertIsInstance(transfer, Transfer)
        self.assertEqual(transfer.operation, 'get')


class TestCommandEmulation(unittest.TestCase):
    """Test command emulation features."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_echo_command(self):
        """Test echo command emulation."""
        conn = Connection('example.com')
        result = conn.run('echo "Hello World"')
        
        self.assertEqual(result.stdout, 'Hello World')
    
    def test_ls_command(self):
        """Test ls command emulation."""
        conn = Connection('example.com')
        result = conn.run('ls -la')
        
        self.assertIn('file', result.stdout)
    
    def test_pwd_command(self):
        """Test pwd command emulation."""
        conn = Connection('example.com')
        result = conn.run('pwd')
        
        self.assertIn('/', result.stdout)
    
    def test_whoami_command(self):
        """Test whoami command emulation."""
        conn = Connection('example.com', user='testuser')
        result = conn.run('whoami')
        
        self.assertEqual(result.stdout, 'testuser')


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete usage scenarios."""
    
    def setUp(self):
        """Clean state before each test."""
        _command_history.clear()
        _file_transfers.clear()
        _connections.clear()
    
    def test_deployment_workflow(self):
        """Test complete deployment workflow."""
        # Connect to server
        with Connection('deploy.example.com', user='deployer') as conn:
            # Upload application files
            conn.put('app.tar.gz', '/tmp/app.tar.gz')
            
            # Extract files
            conn.run('tar -xzf /tmp/app.tar.gz -C /opt/app')
            
            # Install dependencies
            conn.sudo('pip install -r /opt/app/requirements.txt')
            
            # Restart service
            conn.sudo('systemctl restart myapp')
        
        # Verify operations
        self.assertEqual(len(_file_transfers), 1)
        self.assertEqual(len(_command_history), 3)
    
    def test_multi_server_deployment(self):
        """Test deploying to multiple servers."""
        # Create group of servers
        servers = Group(
            'web1.example.com',
            'web2.example.com',
            'web3.example.com',
            user='deployer'
        )
        
        # Upload configuration
        servers.put('config.json', '/etc/myapp/config.json')
        
        # Restart service on all servers
        results = servers.sudo('systemctl restart myapp')
        
        # Verify all succeeded
        self.assertEqual(len(results), 3)
        for result in results.values():
            self.assertTrue(result.ok)
    
    def test_backup_workflow(self):
        """Test backup workflow."""
        conn = Connection('db.example.com', user='backup')
        
        # Create backup
        conn.run('pg_dump mydb > /backups/mydb_$(date +%Y%m%d).sql')
        
        # Download backup
        conn.get('/backups/mydb_20240101.sql', 'local_backup.sql')
        
        # Verify
        self.assertEqual(len(_file_transfers), 1)
        self.assertEqual(_file_transfers[0]['transfer'].operation, 'get')
    
    def test_configuration_update(self):
        """Test configuration update across servers."""
        servers = Group('app1.com', 'app2.com', 'app3.com')
        
        # Upload new configuration
        servers.put('new_config.yml', '/etc/app/config.yml')
        
        # Validate configuration
        results = servers.run('config-validator /etc/app/config.yml')
        
        # Reload application
        servers.sudo('systemctl reload myapp')
        
        # Verify
        self.assertEqual(len(_file_transfers), 3)
        for result in results.values():
            self.assertTrue(result.ok)


if __name__ == '__main__':
    unittest.main()
