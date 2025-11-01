"""TransDepVulScan - Transitive Dependency Vulnerability Scanner"""
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class Vulnerability:
    cve_id: str
    severity: str
    description: str

class TransDepVulScan:
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}
        self.vulnerabilities: Dict[str, List[Vulnerability]] = {}
    
    def add_dependency(self, name: str, deps: List[str]):
        self.dependencies[name] = deps
    
    def add_vulnerability(self, pkg: str, cve_id: str, severity: str, desc: str):
        if pkg not in self.vulnerabilities:
            self.vulnerabilities[pkg] = []
        self.vulnerabilities[pkg].append(Vulnerability(cve_id, severity, desc))
    
    def scan(self, root_pkg: str) -> Dict[str, List[Vulnerability]]:
        found_vulns = {}
        visited = set()
        
        def scan_recursive(pkg: str):
            if pkg in visited:
                return
            visited.add(pkg)
            
            if pkg in self.vulnerabilities:
                found_vulns[pkg] = self.vulnerabilities[pkg]
            
            for dep in self.dependencies.get(pkg, []):
                scan_recursive(dep)
        
        scan_recursive(root_pkg)
        return found_vulns
    
    def get_statistics(self) -> Dict:
        return {'total_packages': len(self.dependencies)}
