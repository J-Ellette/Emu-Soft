#!/usr/bin/env python3
"""
Ansible Emulator - Configuration Management and Automation

This module emulates core Ansible functionality including:
- Inventory management
- Playbook execution
- Task execution
- Module system
- Facts gathering
- Variable management
- Handlers and notifications
- Roles and includes
"""

import json
import yaml
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class TaskState(Enum):
    """Task execution states"""
    OK = "ok"
    CHANGED = "changed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNREACHABLE = "unreachable"


class ModuleResult(Enum):
    """Module execution results"""
    SUCCESS = "success"
    CHANGED = "changed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Host:
    """Inventory host"""
    name: str
    ansible_host: Optional[str] = None
    ansible_port: int = 22
    ansible_user: Optional[str] = None
    vars: Dict[str, Any] = field(default_factory=dict)
    groups: List[str] = field(default_factory=list)


@dataclass
class Group:
    """Inventory group"""
    name: str
    hosts: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    vars: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task execution"""
    host: str
    task_name: str
    state: TaskState
    changed: bool = False
    failed: bool = False
    skipped: bool = False
    msg: str = ""
    stdout: str = ""
    stderr: str = ""
    rc: int = 0
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Ansible task definition"""
    name: str
    module: str
    args: Dict[str, Any] = field(default_factory=dict)
    when: Optional[str] = None
    loop: Optional[List[Any]] = None
    register: Optional[str] = None
    notify: Optional[List[str]] = None
    tags: List[str] = field(default_factory=list)
    become: bool = False
    become_user: str = "root"
    ignore_errors: bool = False
    changed_when: Optional[str] = None
    failed_when: Optional[str] = None


@dataclass
class Handler:
    """Ansible handler definition"""
    name: str
    module: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Play:
    """Ansible play definition"""
    name: str
    hosts: str
    tasks: List[Task] = field(default_factory=list)
    handlers: List[Handler] = field(default_factory=list)
    vars: Dict[str, Any] = field(default_factory=dict)
    gather_facts: bool = True
    become: bool = False
    become_user: str = "root"
    tags: List[str] = field(default_factory=list)


@dataclass
class Playbook:
    """Ansible playbook"""
    name: str
    plays: List[Play] = field(default_factory=list)


class Inventory:
    """Ansible inventory manager"""
    
    def __init__(self):
        self.hosts: Dict[str, Host] = {}
        self.groups: Dict[str, Group] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Create default groups"""
        self.groups["all"] = Group(name="all")
        self.groups["ungrouped"] = Group(name="ungrouped")
    
    def add_host(self, host: Host, groups: Optional[List[str]] = None):
        """Add a host to inventory"""
        self.hosts[host.name] = host
        
        if groups:
            for group_name in groups:
                if group_name not in self.groups:
                    self.groups[group_name] = Group(name=group_name)
                self.groups[group_name].hosts.append(host.name)
                host.groups.append(group_name)
        else:
            self.groups["ungrouped"].hosts.append(host.name)
            host.groups.append("ungrouped")
        
        # Add to 'all' group
        if host.name not in self.groups["all"].hosts:
            self.groups["all"].hosts.append(host.name)
    
    def add_group(self, group: Group):
        """Add a group to inventory"""
        self.groups[group.name] = group
    
    def get_hosts(self, pattern: str = "all") -> List[Host]:
        """Get hosts matching pattern"""
        if pattern == "all":
            return list(self.hosts.values())
        elif pattern in self.groups:
            host_names = self.groups[pattern].hosts
            return [self.hosts[name] for name in host_names if name in self.hosts]
        elif pattern in self.hosts:
            return [self.hosts[pattern]]
        else:
            # Pattern matching (simplified)
            matched = []
            for host_name, host in self.hosts.items():
                if re.match(pattern.replace("*", ".*"), host_name):
                    matched.append(host)
            return matched
    
    def get_group_vars(self, group_name: str) -> Dict[str, Any]:
        """Get variables for a group"""
        if group_name in self.groups:
            return self.groups[group_name].vars.copy()
        return {}
    
    def get_host_vars(self, host_name: str) -> Dict[str, Any]:
        """Get variables for a host (including group vars)"""
        if host_name not in self.hosts:
            return {}
        
        host = self.hosts[host_name]
        vars_dict = {}
        
        # Merge group vars
        for group_name in host.groups:
            vars_dict.update(self.get_group_vars(group_name))
        
        # Apply host vars (override group vars)
        vars_dict.update(host.vars)
        
        return vars_dict


class ModuleLibrary:
    """Ansible module library"""
    
    def __init__(self):
        self.modules: Dict[str, Callable] = {}
        self._register_builtin_modules()
    
    def _register_builtin_modules(self):
        """Register built-in modules"""
        self.modules["ping"] = self._module_ping
        self.modules["command"] = self._module_command
        self.modules["shell"] = self._module_shell
        self.modules["copy"] = self._module_copy
        self.modules["file"] = self._module_file
        self.modules["template"] = self._module_template
        self.modules["service"] = self._module_service
        self.modules["package"] = self._module_package
        self.modules["user"] = self._module_user
        self.modules["group"] = self._module_group
        self.modules["git"] = self._module_git
        self.modules["apt"] = self._module_apt
        self.modules["yum"] = self._module_yum
        self.modules["systemd"] = self._module_systemd
        self.modules["debug"] = self._module_debug
    
    def execute(self, module_name: str, args: Dict[str, Any], 
                host: Host, vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a module"""
        if module_name not in self.modules:
            return {
                "failed": True,
                "msg": f"Module '{module_name}' not found"
            }
        
        try:
            return self.modules[module_name](args, host, vars_dict)
        except Exception as e:
            return {
                "failed": True,
                "msg": str(e)
            }
    
    # Built-in module implementations
    
    def _module_ping(self, args: Dict[str, Any], host: Host, 
                     vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Ping module"""
        return {
            "ping": "pong",
            "changed": False
        }
    
    def _module_command(self, args: Dict[str, Any], host: Host,
                       vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Command module"""
        cmd = args.get("_raw_params", args.get("cmd", ""))
        return {
            "cmd": cmd,
            "stdout": f"Executed: {cmd}",
            "stderr": "",
            "rc": 0,
            "changed": True
        }
    
    def _module_shell(self, args: Dict[str, Any], host: Host,
                     vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Shell module"""
        cmd = args.get("_raw_params", args.get("cmd", ""))
        return {
            "cmd": cmd,
            "stdout": f"Executed via shell: {cmd}",
            "stderr": "",
            "rc": 0,
            "changed": True
        }
    
    def _module_copy(self, args: Dict[str, Any], host: Host,
                    vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Copy module"""
        src = args.get("src", "")
        dest = args.get("dest", "")
        return {
            "src": src,
            "dest": dest,
            "changed": True,
            "msg": f"Copied {src} to {dest}"
        }
    
    def _module_file(self, args: Dict[str, Any], host: Host,
                    vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """File module"""
        path = args.get("path", "")
        state = args.get("state", "file")
        return {
            "path": path,
            "state": state,
            "changed": True,
            "msg": f"File {path} is {state}"
        }
    
    def _module_template(self, args: Dict[str, Any], host: Host,
                        vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Template module"""
        src = args.get("src", "")
        dest = args.get("dest", "")
        return {
            "src": src,
            "dest": dest,
            "changed": True,
            "msg": f"Templated {src} to {dest}"
        }
    
    def _module_service(self, args: Dict[str, Any], host: Host,
                       vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Service module"""
        name = args.get("name", "")
        state = args.get("state", "started")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"Service {name} is {state}"
        }
    
    def _module_package(self, args: Dict[str, Any], host: Host,
                       vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Package module"""
        name = args.get("name", "")
        state = args.get("state", "present")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"Package {name} is {state}"
        }
    
    def _module_user(self, args: Dict[str, Any], host: Host,
                    vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """User module"""
        name = args.get("name", "")
        state = args.get("state", "present")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"User {name} is {state}"
        }
    
    def _module_group(self, args: Dict[str, Any], host: Host,
                     vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Group module"""
        name = args.get("name", "")
        state = args.get("state", "present")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"Group {name} is {state}"
        }
    
    def _module_git(self, args: Dict[str, Any], host: Host,
                   vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Git module"""
        repo = args.get("repo", "")
        dest = args.get("dest", "")
        version = args.get("version", "HEAD")
        return {
            "repo": repo,
            "dest": dest,
            "version": version,
            "changed": True,
            "msg": f"Cloned {repo} to {dest}"
        }
    
    def _module_apt(self, args: Dict[str, Any], host: Host,
                   vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """APT module"""
        name = args.get("name", "")
        state = args.get("state", "present")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"Package {name} is {state} (apt)"
        }
    
    def _module_yum(self, args: Dict[str, Any], host: Host,
                   vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """YUM module"""
        name = args.get("name", "")
        state = args.get("state", "present")
        return {
            "name": name,
            "state": state,
            "changed": True,
            "msg": f"Package {name} is {state} (yum)"
        }
    
    def _module_systemd(self, args: Dict[str, Any], host: Host,
                       vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Systemd module"""
        name = args.get("name", "")
        state = args.get("state", "started")
        enabled = args.get("enabled", None)
        return {
            "name": name,
            "state": state,
            "enabled": enabled,
            "changed": True,
            "msg": f"Service {name} is {state}"
        }
    
    def _module_debug(self, args: Dict[str, Any], host: Host,
                     vars_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Debug module"""
        msg = args.get("msg", "")
        var = args.get("var", None)
        
        if var:
            value = vars_dict.get(var, f"VARIABLE NOT DEFINED: {var}")
            return {
                "msg": f"{var}: {value}",
                "changed": False
            }
        return {
            "msg": msg,
            "changed": False
        }


class AnsibleEmulator:
    """Main Ansible emulator class"""
    
    def __init__(self):
        self.inventory = Inventory()
        self.module_library = ModuleLibrary()
        self.facts: Dict[str, Dict[str, Any]] = {}
        self.playbook_results: List[Dict[str, Any]] = []
    
    def gather_facts(self, host: Host) -> Dict[str, Any]:
        """Gather facts from a host"""
        facts = {
            "ansible_hostname": host.name,
            "ansible_host": host.ansible_host or host.name,
            "ansible_port": host.ansible_port,
            "ansible_user": host.ansible_user or "ansible",
            "ansible_os_family": "Linux",
            "ansible_distribution": "Ubuntu",
            "ansible_distribution_version": "20.04",
            "ansible_python_version": "3.8.10",
            "ansible_architecture": "x86_64",
            "ansible_processor_cores": 4,
            "ansible_memtotal_mb": 8192,
            "ansible_interfaces": ["eth0", "lo"],
            "ansible_default_ipv4": {
                "address": "192.168.1.100",
                "interface": "eth0"
            }
        }
        
        self.facts[host.name] = facts
        return facts
    
    def evaluate_condition(self, condition: str, vars_dict: Dict[str, Any]) -> bool:
        """Evaluate a when condition (simplified)"""
        if not condition:
            return True
        
        # Simple boolean checks
        if condition == "true":
            return True
        if condition == "false":
            return False
        
        # Variable checks
        for var_name, var_value in vars_dict.items():
            condition = condition.replace(var_name, str(var_value))
        
        # Very basic evaluation (not secure, for emulation only)
        try:
            # Only allow simple comparisons
            if any(op in condition for op in ["==", "!=", ">", "<", ">=", "<="]):
                return eval(condition, {"__builtins__": {}}, {})
        except:
            pass
        
        return True
    
    def execute_task(self, task: Task, host: Host, 
                    vars_dict: Dict[str, Any]) -> TaskResult:
        """Execute a single task on a host"""
        # Check condition
        if task.when and not self.evaluate_condition(task.when, vars_dict):
            return TaskResult(
                host=host.name,
                task_name=task.name,
                state=TaskState.SKIPPED,
                skipped=True,
                msg="Skipped due to when condition"
            )
        
        # Handle loops
        if task.loop:
            results = []
            for item in task.loop:
                item_vars = vars_dict.copy()
                item_vars["item"] = item
                module_result = self.module_library.execute(
                    task.module, task.args, host, item_vars
                )
                results.append(module_result)
            
            # Aggregate results
            any_changed = any(r.get("changed", False) for r in results)
            any_failed = any(r.get("failed", False) for r in results)
            
            if any_failed and not task.ignore_errors:
                return TaskResult(
                    host=host.name,
                    task_name=task.name,
                    state=TaskState.FAILED,
                    failed=True,
                    msg="Task failed in loop",
                    results={"results": results}
                )
            
            return TaskResult(
                host=host.name,
                task_name=task.name,
                state=TaskState.CHANGED if any_changed else TaskState.OK,
                changed=any_changed,
                msg=f"Executed {len(results)} items in loop",
                results={"results": results}
            )
        
        # Execute single task
        module_result = self.module_library.execute(
            task.module, task.args, host, vars_dict
        )
        
        # Determine state
        changed = module_result.get("changed", False)
        failed = module_result.get("failed", False)
        
        if failed and not task.ignore_errors:
            state = TaskState.FAILED
        elif changed:
            state = TaskState.CHANGED
        else:
            state = TaskState.OK
        
        result = TaskResult(
            host=host.name,
            task_name=task.name,
            state=state,
            changed=changed,
            failed=failed,
            msg=module_result.get("msg", ""),
            stdout=module_result.get("stdout", ""),
            stderr=module_result.get("stderr", ""),
            rc=module_result.get("rc", 0),
            results=module_result
        )
        
        # Store registered variable
        if task.register:
            vars_dict[task.register] = module_result
        
        return result
    
    def execute_play(self, play: Play) -> Dict[str, Any]:
        """Execute a play"""
        play_results = {
            "play_name": play.name,
            "hosts": [],
            "tasks": [],
            "handlers": []
        }
        
        # Get target hosts
        hosts = self.inventory.get_hosts(play.hosts)
        play_results["hosts"] = [h.name for h in hosts]
        
        notified_handlers: Dict[str, List[str]] = {}  # handler_name -> [host_names]
        
        for host in hosts:
            # Gather facts
            if play.gather_facts:
                facts = self.gather_facts(host)
                host.vars.update(facts)
            
            # Build variable context
            vars_dict = {}
            vars_dict.update(play.vars)
            vars_dict.update(self.inventory.get_host_vars(host.name))
            
            # Execute tasks
            for task in play.tasks:
                result = self.execute_task(task, host, vars_dict)
                play_results["tasks"].append(result)
                
                # Track handler notifications
                if task.notify and result.changed:
                    for handler_name in task.notify:
                        if handler_name not in notified_handlers:
                            notified_handlers[handler_name] = []
                        notified_handlers[handler_name].append(host.name)
        
        # Execute notified handlers
        for handler in play.handlers:
            if handler.name in notified_handlers:
                for host_name in notified_handlers[handler.name]:
                    if host_name in self.inventory.hosts:
                        host = self.inventory.hosts[host_name]
                        vars_dict = {}
                        vars_dict.update(play.vars)
                        vars_dict.update(self.inventory.get_host_vars(host.name))
                        
                        # Execute handler as a task
                        handler_task = Task(
                            name=handler.name,
                            module=handler.module,
                            args=handler.args
                        )
                        result = self.execute_task(handler_task, host, vars_dict)
                        play_results["handlers"].append(result)
        
        return play_results
    
    def run_playbook(self, playbook: Playbook) -> Dict[str, Any]:
        """Run a complete playbook"""
        playbook_results = {
            "playbook_name": playbook.name,
            "plays": [],
            "summary": {
                "ok": 0,
                "changed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
        
        for play in playbook.plays:
            play_result = self.execute_play(play)
            playbook_results["plays"].append(play_result)
            
            # Update summary
            for task_result in play_result["tasks"]:
                if task_result.state == TaskState.OK:
                    playbook_results["summary"]["ok"] += 1
                elif task_result.state == TaskState.CHANGED:
                    playbook_results["summary"]["changed"] += 1
                elif task_result.state == TaskState.FAILED:
                    playbook_results["summary"]["failed"] += 1
                elif task_result.state == TaskState.SKIPPED:
                    playbook_results["summary"]["skipped"] += 1
        
        self.playbook_results.append(playbook_results)
        return playbook_results
    
    def run_ad_hoc(self, module: str, args: Dict[str, Any], 
                   pattern: str = "all") -> List[TaskResult]:
        """Run an ad-hoc command"""
        hosts = self.inventory.get_hosts(pattern)
        results = []
        
        for host in hosts:
            vars_dict = self.inventory.get_host_vars(host.name)
            task = Task(name=f"ad-hoc {module}", module=module, args=args)
            result = self.execute_task(task, host, vars_dict)
            results.append(result)
        
        return results


# Example usage
if __name__ == "__main__":
    # Create Ansible emulator
    ansible = AnsibleEmulator()
    
    # Add hosts to inventory
    web1 = Host(name="web1", ansible_host="192.168.1.10", vars={"env": "prod"})
    web2 = Host(name="web2", ansible_host="192.168.1.11", vars={"env": "prod"})
    db1 = Host(name="db1", ansible_host="192.168.1.20", vars={"env": "prod"})
    
    ansible.inventory.add_host(web1, groups=["webservers"])
    ansible.inventory.add_host(web2, groups=["webservers"])
    ansible.inventory.add_host(db1, groups=["databases"])
    
    # Create a playbook
    playbook = Playbook(name="Deploy Web Application")
    
    # Define play
    play = Play(
        name="Configure web servers",
        hosts="webservers",
        vars={"app_version": "1.0", "app_port": 8080}
    )
    
    # Add tasks
    play.tasks = [
        Task(name="Install nginx", module="apt", 
             args={"name": "nginx", "state": "present"}),
        Task(name="Copy config", module="copy",
             args={"src": "/local/nginx.conf", "dest": "/etc/nginx/nginx.conf"},
             notify=["restart nginx"]),
        Task(name="Ensure nginx is running", module="service",
             args={"name": "nginx", "state": "started", "enabled": True})
    ]
    
    # Add handler
    play.handlers = [
        Handler(name="restart nginx", module="service",
               args={"name": "nginx", "state": "restarted"})
    ]
    
    playbook.plays.append(play)
    
    # Run playbook
    result = ansible.run_playbook(playbook)
    
    print(f"Playbook: {result['playbook_name']}")
    print(f"Summary: {result['summary']}")
    
    # Run ad-hoc command
    print("\nRunning ad-hoc ping:")
    ping_results = ansible.run_ad_hoc("ping", {}, "all")
    for r in ping_results:
        print(f"  {r.host}: {r.state.value}")
