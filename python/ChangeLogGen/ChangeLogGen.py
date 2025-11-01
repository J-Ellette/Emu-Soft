"""ChangeLogGen - Changelog generator from git commits"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChangeEntry:
    type: str  # 'feature', 'fix', 'breaking'
    message: str
    commit_sha: str
    author: str
    date: str

class ChangeLogGen:
    def __init__(self):
        self.entries: List[ChangeEntry] = []
    
    def add_commit(self, commit_sha: str, message: str, author: str = "Unknown"):
        change_type = self._classify_commit(message)
        entry = ChangeEntry(
            type=change_type,
            message=message,
            commit_sha=commit_sha,
            author=author,
            date=datetime.utcnow().isoformat()
        )
        self.entries.append(entry)
    
    def _classify_commit(self, message: str) -> str:
        msg_lower = message.lower()
        if 'breaking' in msg_lower or 'major' in msg_lower:
            return 'breaking'
        elif 'fix' in msg_lower or 'bug' in msg_lower:
            return 'fix'
        elif 'feat' in msg_lower or 'add' in msg_lower:
            return 'feature'
        return 'other'
    
    def generate_changelog(self, version: str = "1.0.0") -> str:
        lines = [f"# Changelog - Version {version}\n"]
        
        by_type = {'breaking': [], 'feature': [], 'fix': [], 'other': []}
        for entry in self.entries:
            by_type[entry.type].append(entry)
        
        if by_type['breaking']:
            lines.append("## Breaking Changes\n")
            for e in by_type['breaking']:
                lines.append(f"- {e.message} ({e.commit_sha[:7]})\n")
        
        if by_type['feature']:
            lines.append("## Features\n")
            for e in by_type['feature']:
                lines.append(f"- {e.message} ({e.commit_sha[:7]})\n")
        
        if by_type['fix']:
            lines.append("## Bug Fixes\n")
            for e in by_type['fix']:
                lines.append(f"- {e.message} ({e.commit_sha[:7]})\n")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {'total_commits': len(self.entries)}
