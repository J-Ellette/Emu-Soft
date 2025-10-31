#!/usr/bin/env python3
"""
Test suite for Ansible Emulator
"""

import unittest
from ConfigMan import (
    ConfigMan, Host, Group, Task, Play, Playbook, Handler,
    TaskState, Inventory
)


class TestConfigMan(unittest.TestCase):
    """Test cases for Ansible emulator"""
    
    def setUp(self):
        """Set up test instance"""
        self.ansible = ConfigMan()
    
    def test_inventory_add_host(self):
        """Test adding hosts to inventory"""
        host = Host(name="server1", ansible_host="192.168.1.10")
        self.ansible.inventory.add_host(host, groups=["webservers"])
        
        self.assertIn("server1", self.ansible.inventory.hosts)
        self.assertIn("webservers", self.ansible.inventory.groups)
    
    def test_inventory_get_hosts(self):
        """Test getting hosts by pattern"""
        host1 = Host(name="web1")
        host2 = Host(name="web2")
        
        self.ansible.inventory.add_host(host1, groups=["webservers"])
        self.ansible.inventory.add_host(host2, groups=["webservers"])
        
        hosts = self.ansible.inventory.get_hosts("webservers")
        self.assertEqual(len(hosts), 2)
    
    def test_execute_task_ping(self):
        """Test executing ping task"""
        host = Host(name="server1")
        self.ansible.inventory.add_host(host)
        
        task = Task(name="Ping server", module="ping", args={})
        result = self.ansible.execute_task(task, host, {})
        
        self.assertEqual(result.host, "server1")
        self.assertEqual(result.state, TaskState.OK)
        self.assertFalse(result.failed)
    
    def test_execute_task_with_loop(self):
        """Test task execution with loop"""
        host = Host(name="server1")
        task = Task(
            name="Install packages",
            module="apt",
            args={"name": "{{ item }}", "state": "present"},
            loop=["nginx", "python3", "git"]
        )
        
        result = self.ansible.execute_task(task, host, {})
        self.assertEqual(result.state, TaskState.CHANGED)
        self.assertTrue(result.changed)
    
    def test_execute_play(self):
        """Test play execution"""
        host1 = Host(name="web1")
        host2 = Host(name="web2")
        self.ansible.inventory.add_host(host1, groups=["webservers"])
        self.ansible.inventory.add_host(host2, groups=["webservers"])
        
        play = Play(name="Configure servers", hosts="webservers")
        play.tasks = [
            Task(name="Install nginx", module="apt", 
                 args={"name": "nginx", "state": "present"})
        ]
        
        result = self.ansible.execute_play(play)
        
        self.assertEqual(result["play_name"], "Configure servers")
        self.assertEqual(len(result["hosts"]), 2)
        self.assertGreater(len(result["tasks"]), 0)
    
    def test_run_playbook(self):
        """Test running complete playbook"""
        host = Host(name="server1")
        self.ansible.inventory.add_host(host, groups=["all"])
        
        playbook = Playbook(name="Test Playbook")
        play = Play(name="Test Play", hosts="all")
        play.tasks = [
            Task(name="Ping", module="ping", args={})
        ]
        playbook.plays.append(play)
        
        result = self.ansible.run_playbook(playbook)
        
        self.assertEqual(result["playbook_name"], "Test Playbook")
        self.assertIn("summary", result)
        self.assertGreater(result["summary"]["ok"], 0)
    
    def test_run_ad_hoc(self):
        """Test ad-hoc command execution"""
        host = Host(name="server1")
        self.ansible.inventory.add_host(host)
        
        results = self.ansible.run_ad_hoc("ping", {}, "all")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].host, "server1")
        self.assertEqual(results[0].state, TaskState.OK)
    
    def test_gather_facts(self):
        """Test facts gathering"""
        host = Host(name="server1")
        facts = self.ansible.gather_facts(host)
        
        self.assertIn("ansible_hostname", facts)
        self.assertIn("ansible_os_family", facts)
        self.assertEqual(facts["ansible_hostname"], "server1")
    
    def test_handler_notification(self):
        """Test handler notifications"""
        host = Host(name="server1")
        self.ansible.inventory.add_host(host, groups=["all"])
        
        play = Play(name="Test handlers", hosts="all")
        play.tasks = [
            Task(name="Copy config", module="copy",
                 args={"src": "test", "dest": "/etc/test"},
                 notify=["restart service"])
        ]
        play.handlers = [
            Handler(name="restart service", module="service",
                   args={"name": "test", "state": "restarted"})
        ]
        
        result = self.ansible.execute_play(play)
        self.assertGreater(len(result["handlers"]), 0)


if __name__ == "__main__":
    unittest.main()
