"""MultiRepRef - Multi-Repo Refactoring Coordinator"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RefactorTask:
    repo: str
    file: str
    changes: str
    status: str = 'pending'

class MultiRepRef:
    def __init__(self):
        self.tasks: List[RefactorTask] = []
    
    def add_task(self, repo: str, file: str, changes: str):
        self.tasks.append(RefactorTask(repo, file, changes))
    
    def mark_complete(self, repo: str, file: str):
        for task in self.tasks:
            if task.repo == repo and task.file == file:
                task.status = 'complete'
    
    def get_progress(self) -> Dict:
        completed = sum(1 for t in self.tasks if t.status == 'complete')
        return {
            'total': len(self.tasks),
            'completed': completed,
            'pending': len(self.tasks) - completed
        }
