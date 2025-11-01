"""DataMig - Database Migration Rollback Safety Checker"""
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Migration:
    id: str
    up_sql: str
    down_sql: str
    reversible: bool = True

class DataMig:
    def __init__(self):
        self.migrations: List[Migration] = []
    
    def add_migration(self, id: str, up_sql: str, down_sql: Optional[str] = None):
        reversible = down_sql is not None and len(down_sql.strip()) > 0
        self.migrations.append(Migration(id, up_sql, down_sql or "", reversible))
    
    def check_rollback_safety(self) -> Dict[str, List[str]]:
        safe = []
        unsafe = []
        
        for mig in self.migrations:
            if mig.reversible:
                safe.append(mig.id)
            else:
                unsafe.append(mig.id)
        
        return {'safe': safe, 'unsafe': unsafe}
    
    def get_statistics(self) -> Dict:
        return {'total_migrations': len(self.migrations)}
