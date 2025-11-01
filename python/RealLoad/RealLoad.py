"""RealLoad - Realistic Load Pattern Generator"""
from typing import List, Dict
from dataclasses import dataclass
import random

@dataclass
class LoadPattern:
    name: str
    requests_per_second: int
    duration_seconds: int

class RealLoad:
    def __init__(self):
        self.patterns: List[LoadPattern] = []
    
    def add_pattern(self, name: str, rps: int, duration: int):
        self.patterns.append(LoadPattern(name, rps, duration))
    
    def generate_traffic(self, pattern_name: str) -> List[float]:
        pattern = next((p for p in self.patterns if p.name == pattern_name), None)
        if not pattern:
            return []
        
        timestamps = []
        for _ in range(pattern.requests_per_second * pattern.duration_seconds):
            timestamps.append(random.uniform(0, pattern.duration_seconds))
        return sorted(timestamps)
    
    def get_statistics(self) -> Dict:
        return {'total_patterns': len(self.patterns)}
