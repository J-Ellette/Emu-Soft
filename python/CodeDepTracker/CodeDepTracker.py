"""CodeDepTracker - Code Deprecation Tracker"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DeprecatedAPI:
    name: str
    version: str
    replacement: str
    usages: List[str] = None

class CodeDepTracker:
    def __init__(self):
        self.deprecated_apis: Dict[str, DeprecatedAPI] = {}
    
    def mark_deprecated(self, name: str, version: str, replacement: str):
        self.deprecated_apis[name] = DeprecatedAPI(name, version, replacement, [])
    
    def record_usage(self, api_name: str, location: str):
        if api_name in self.deprecated_apis:
            self.deprecated_apis[api_name].usages.append(location)
    
    def get_report(self) -> Dict[str, List]:
        return {
            api: {
                'replacement': info.replacement,
                'usage_count': len(info.usages),
                'locations': info.usages
            }
            for api, info in self.deprecated_apis.items()
            if info.usages
        }
    
    def get_statistics(self) -> Dict:
        return {'total_deprecated': len(self.deprecated_apis)}
