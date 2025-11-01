"""BuildCacheOpt - Build Cache Optimizer"""
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class CacheEntry:
    key: str
    size_mb: float
    hit_count: int = 0

class BuildCacheOpt:
    def __init__(self, max_size_mb: float = 1000):
        self.max_size_mb = max_size_mb
        self.cache: Dict[str, CacheEntry] = {}
    
    def add_entry(self, key: str, size_mb: float):
        self.cache[key] = CacheEntry(key, size_mb)
    
    def record_hit(self, key: str):
        if key in self.cache:
            self.cache[key].hit_count += 1
    
    def optimize(self) -> List[str]:
        total_size = sum(e.size_mb for e in self.cache.values())
        if total_size <= self.max_size_mb:
            return []
        
        # Sort by hit count (keep most used)
        sorted_entries = sorted(self.cache.values(), key=lambda e: e.hit_count)
        
        to_remove = []
        removed_size = 0
        for entry in sorted_entries:
            if total_size - removed_size <= self.max_size_mb:
                break
            to_remove.append(entry.key)
            removed_size += entry.size_mb
        
        return to_remove
    
    def get_statistics(self) -> Dict:
        return {
            'total_entries': len(self.cache),
            'total_size_mb': sum(e.size_mb for e in self.cache.values())
        }
