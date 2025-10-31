"""
Fabric Emulator - SSH Deployment Automation Tool

This module emulates the Fabric library, which is a high-level Python library
designed to execute shell commands remotely over SSH, simplifying deployment
and system administration tasks.

Key Features:
- Remote command execution
- File transfer (upload/download)
- Connection management
- Task execution
- Context managers for configuration
- Group operations on multiple hosts
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import re
import os


class FabricError(Exception):
    """Base exception for Fabric errors."""
    pass


class ConnectionError(FabricError):
    """Raised when connection fails."""
    pass


class CommandError(FabricError):
    """Raised when a command fails."""
    pass


class TransferError(FabricError):
    """Raised when file transfer fails."""
    pass


# In-memory storage for emulated operations
_command_history: List[Dict[str, Any]] = []
_file_transfers: List[Dict[str, Any]] = []
_connections: Dict[str, Dict[str, Any]] = {}


@dataclass
class Result:
    """Result of a command execution."""
    
    command: str
    stdout: str = ""
    stderr: str = ""
    exited: int = 0
    ok: bool = True
    failed: bool = False
    return_code: int = 0
    encoding: str = "utf-8"
    hide: Optional[tuple] = None
    
    def __post_init__(self):
        self.ok = self.exited == 0
        self.failed = not self.ok
        self.return_code = self.exited
    
    def __bool__(self):
        return self.ok
    
    def __str__(self):
        return self.stdout


@dataclass
class Transfer:
    """Result of a file transfer operation."""
    
    local: str
    remote: str
    operation: str  # 'put' or 'get'
    success: bool = True
    bytes_transferred: int = 0
    
    def __bool__(self):
        return self.success


class Connection:
    """SSH connection to a remote host."""
    
    def __init__(
        self,
        host: str,
        user: Optional[str] = None,
        port: int = 22,
        config: Optional[Config] = None,
        gateway: Optional[Connection] = None,
        forward_agent: bool = False,
        connect_timeout: Optional[int] = None,
        connect_kwargs: Optional[Dict[str, Any]] = None,
        inline_ssh_env: bool = False
    ):
        """
        Initialize SSH connection.
        
        Args:
            host: Hostname or IP address
            user: Username for authentication
            port: SSH port (default: 22)
            config: Configuration object
            gateway: Gateway connection for proxy
            forward_agent: Enable SSH agent forwarding
            connect_timeout: Connection timeout in seconds
            connect_kwargs: Additional connection parameters
            inline_ssh_env: Use inline environment variables
        """
        self.host = host
        self.user = user or 'root'
        self.port = port
        self.config = config or Config()
        self.gateway = gateway
        self.forward_agent = forward_agent
        self.connect_timeout = connect_timeout
        self.connect_kwargs = connect_kwargs or {}
        self.inline_ssh_env = inline_ssh_env
        
        self.is_connected = False
        self.connection_id = f"{self.user}@{self.host}:{self.port}"
        
        # Store connection info
        _connections[self.connection_id] = {
            'host': self.host,
            'user': self.user,
            'port': self.port,
            'connected_at': datetime.utcnow().isoformat(),
            'commands_executed': 0
        }
    
    def open(self):
        """Open the connection."""
        self.is_connected = True
        return self
    
    def close(self):
        """Close the connection."""
        self.is_connected = False
    
    def run(
        self,
        command: str,
        warn: bool = False,
        hide: bool = False,
        pty: bool = True,
        echo: bool = False,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Result:
        """
        Execute a shell command on the remote host.
        
        Args:
            command: Command to execute
            warn: Don't raise exception on failure
            hide: Hide output
            pty: Request a pseudo-terminal
            echo: Echo command before running
            env: Environment variables
            **kwargs: Additional options
        
        Returns:
            Result object
        """
        if not self.is_connected:
            self.open()
        
        # Emulate command execution
        result_data = self._emulate_command(command, env)
        
        # Create result object
        result = Result(
            command=command,
            stdout=result_data.get('stdout', ''),
            stderr=result_data.get('stderr', ''),
            exited=result_data.get('exit_code', 0),
            hide=('stdout', 'stderr') if hide else None
        )
        
        # Log command
        _command_history.append({
            'connection': self.connection_id,
            'command': command,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update connection stats
        _connections[self.connection_id]['commands_executed'] += 1
        
        if not warn and result.failed:
            raise CommandError(f"Command failed: {command}")
        
        return result
    
    def sudo(
        self,
        command: str,
        user: Optional[str] = None,
        warn: bool = False,
        **kwargs
    ) -> Result:
        """
        Execute a command with sudo.
        
        Args:
            command: Command to execute
            user: User to run as (default: root)
            warn: Don't raise exception on failure
            **kwargs: Additional options
        
        Returns:
            Result object
        """
        sudo_command = f"sudo -u {user or 'root'} {command}"
        return self.run(sudo_command, warn=warn, **kwargs)
    
    def local(self, command: str, **kwargs) -> Result:
        """
        Execute a command locally (on the machine running Fabric).
        
        Args:
            command: Command to execute
            **kwargs: Additional options
        
        Returns:
            Result object
        """
        # Emulate local command execution
        result_data = self._emulate_command(command, {})
        
        return Result(
            command=command,
            stdout=result_data.get('stdout', ''),
            stderr=result_data.get('stderr', ''),
            exited=result_data.get('exit_code', 0)
        )
    
    def put(
        self,
        local: str,
        remote: Optional[str] = None,
        preserve_mode: bool = True
    ) -> Transfer:
        """
        Upload a file to the remote host.
        
        Args:
            local: Local file path
            remote: Remote file path (default: same as local)
            preserve_mode: Preserve file mode
        
        Returns:
            Transfer object
        """
        if not self.is_connected:
            self.open()
        
        remote = remote or local
        
        # Emulate file size
        bytes_transferred = len(local) * 100  # Fake size
        
        transfer = Transfer(
            local=local,
            remote=remote,
            operation='put',
            success=True,
            bytes_transferred=bytes_transferred
        )
        
        _file_transfers.append({
            'connection': self.connection_id,
            'transfer': transfer,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return transfer
    
    def get(
        self,
        remote: str,
        local: Optional[str] = None,
        preserve_mode: bool = True
    ) -> Transfer:
        """
        Download a file from the remote host.
        
        Args:
            remote: Remote file path
            local: Local file path (default: same as remote)
            preserve_mode: Preserve file mode
        
        Returns:
            Transfer object
        """
        if not self.is_connected:
            self.open()
        
        local = local or remote
        
        # Emulate file size
        bytes_transferred = len(remote) * 100  # Fake size
        
        transfer = Transfer(
            local=local,
            remote=remote,
            operation='get',
            success=True,
            bytes_transferred=bytes_transferred
        )
        
        _file_transfers.append({
            'connection': self.connection_id,
            'transfer': transfer,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return transfer
    
    def _emulate_command(self, command: str, env: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Emulate command execution and return simulated results."""
        # Simple command emulation
        if 'echo' in command.lower():
            # Extract text after echo
            match = re.search(r'echo\s+(.+)', command, re.IGNORECASE)
            if match:
                output = match.group(1).strip('\'"')
                return {'stdout': output, 'stderr': '', 'exit_code': 0}
        
        if 'ls' in command.lower():
            return {'stdout': 'file1.txt\nfile2.txt\ndir1/', 'stderr': '', 'exit_code': 0}
        
        if 'pwd' in command.lower():
            return {'stdout': '/home/user', 'stderr': '', 'exit_code': 0}
        
        if 'whoami' in command.lower():
            return {'stdout': self.user, 'stderr': '', 'exit_code': 0}
        
        if 'uname' in command.lower():
            return {'stdout': 'Linux', 'stderr': '', 'exit_code': 0}
        
        if 'date' in command.lower():
            return {'stdout': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'stderr': '', 'exit_code': 0}
        
        # Default successful execution
        return {
            'stdout': f'Command executed: {command}',
            'stderr': '',
            'exit_code': 0
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class Config:
    """Configuration for Fabric operations."""
    
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            overrides: Configuration overrides
        """
        self.overrides = overrides or {}
        self.run = RunConfig()
        self.sudo = SudoConfig()
        self.timeouts = TimeoutConfig()
    
    def clone(self) -> Config:
        """Create a copy of the configuration."""
        return Config(overrides=self.overrides.copy())


@dataclass
class RunConfig:
    """Configuration for run operations."""
    
    warn: bool = False
    hide: bool = False
    pty: bool = True
    echo: bool = False
    env: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        self.env = self.env or {}


@dataclass
class SudoConfig:
    """Configuration for sudo operations."""
    
    user: str = "root"
    password: Optional[str] = None


@dataclass
class TimeoutConfig:
    """Configuration for timeouts."""
    
    connect: Optional[int] = None
    command: Optional[int] = None


class Group:
    """Manage multiple connections as a group."""
    
    def __init__(
        self,
        *hosts: str,
        user: Optional[str] = None,
        port: int = 22,
        config: Optional[Config] = None
    ):
        """
        Initialize a group of connections.
        
        Args:
            *hosts: Host addresses
            user: Username for all hosts
            port: SSH port for all hosts
            config: Configuration object
        """
        self.hosts = hosts
        self.user = user
        self.port = port
        self.config = config or Config()
        
        self.connections = [
            Connection(host, user=user, port=port, config=self.config)
            for host in hosts
        ]
    
    def run(self, command: str, **kwargs) -> Dict[str, Result]:
        """
        Run command on all hosts.
        
        Args:
            command: Command to execute
            **kwargs: Additional options
        
        Returns:
            Dictionary mapping hosts to results
        """
        results = {}
        for conn in self.connections:
            try:
                results[conn.host] = conn.run(command, **kwargs)
            except Exception as e:
                results[conn.host] = Result(
                    command=command,
                    stderr=str(e),
                    exited=1
                )
        return results
    
    def sudo(self, command: str, **kwargs) -> Dict[str, Result]:
        """
        Run sudo command on all hosts.
        
        Args:
            command: Command to execute
            **kwargs: Additional options
        
        Returns:
            Dictionary mapping hosts to results
        """
        results = {}
        for conn in self.connections:
            try:
                results[conn.host] = conn.sudo(command, **kwargs)
            except Exception as e:
                results[conn.host] = Result(
                    command=command,
                    stderr=str(e),
                    exited=1
                )
        return results
    
    def put(self, local: str, remote: Optional[str] = None, **kwargs) -> Dict[str, Transfer]:
        """
        Upload file to all hosts.
        
        Args:
            local: Local file path
            remote: Remote file path
            **kwargs: Additional options
        
        Returns:
            Dictionary mapping hosts to transfers
        """
        results = {}
        for conn in self.connections:
            results[conn.host] = conn.put(local, remote, **kwargs)
        return results
    
    def close(self):
        """Close all connections."""
        for conn in self.connections:
            conn.close()


class SerialGroup(Group):
    """Execute operations serially on a group of hosts."""
    pass


class ThreadingGroup(Group):
    """Execute operations in parallel using threads."""
    pass


# Task decorator
def task(func: Callable) -> Callable:
    """
    Decorator to mark a function as a Fabric task.
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function
    """
    func.is_task = True
    return func


# Module-level convenience functions
def run(command: str, host: str, **kwargs) -> Result:
    """
    Run a command on a remote host.
    
    Args:
        command: Command to execute
        host: Host address
        **kwargs: Additional options
    
    Returns:
        Result object
    """
    conn = Connection(host, **kwargs)
    return conn.run(command, **kwargs)


def sudo(command: str, host: str, **kwargs) -> Result:
    """
    Run a sudo command on a remote host.
    
    Args:
        command: Command to execute
        host: Host address
        **kwargs: Additional options
    
    Returns:
        Result object
    """
    conn = Connection(host, **kwargs)
    return conn.sudo(command, **kwargs)


def put(local: str, remote: str, host: str, **kwargs) -> Transfer:
    """
    Upload a file to a remote host.
    
    Args:
        local: Local file path
        remote: Remote file path
        host: Host address
        **kwargs: Additional options
    
    Returns:
        Transfer object
    """
    conn = Connection(host, **kwargs)
    return conn.put(local, remote, **kwargs)


def get(remote: str, local: str, host: str, **kwargs) -> Transfer:
    """
    Download a file from a remote host.
    
    Args:
        remote: Remote file path
        local: Local file path
        host: Host address
        **kwargs: Additional options
    
    Returns:
        Transfer object
    """
    conn = Connection(host, **kwargs)
    return conn.get(remote, local, **kwargs)
