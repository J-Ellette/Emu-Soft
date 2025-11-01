"""SBOMsAway - SBOM Generator"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Component:
    name: str
    version: str
    license: str
    dependencies: List[str] = None

class SBOMsAway:
    def __init__(self):
        self.components: Dict[str, Component] = {}
    
    def add_component(self, name: str, version: str, license: str = "Unknown", deps: List[str] = None):
        self.components[name] = Component(name, version, license, deps or [])
    
    def generate_sbom(self, format: str = 'json') -> str:
        import json
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'components': [
                {'name': c.name, 'version': c.version, 'license': c.license, 'dependencies': c.dependencies}
                for c in self.components.values()
            ]
        }
        return json.dumps(data, indent=2) if format == 'json' else str(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {'total_components': len(self.components)}
