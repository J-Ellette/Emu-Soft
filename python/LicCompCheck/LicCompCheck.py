"""LicCompCheck - License Compliance Checker"""
from typing import List, Dict, Set

class LicCompCheck:
    def __init__(self):
        self.allowed_licenses: Set[str] = set()
        self.denied_licenses: Set[str] = set()
        self.components: Dict[str, str] = {}
    
    def set_policy(self, allowed: List[str] = None, denied: List[str] = None):
        self.allowed_licenses = set(allowed or [])
        self.denied_licenses = set(denied or [])
    
    def add_component(self, name: str, license: str):
        self.components[name] = license
    
    def check_compliance(self) -> Dict[str, List[str]]:
        violations = []
        compliant = []
        
        for name, lic in self.components.items():
            if lic in self.denied_licenses:
                violations.append(f"{name}: {lic} (denied)")
            elif self.allowed_licenses and lic not in self.allowed_licenses:
                violations.append(f"{name}: {lic} (not in allowed list)")
            else:
                compliant.append(name)
        
        return {'violations': violations, 'compliant': compliant}
