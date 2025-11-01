"""PipeCost - Pipeline Cost Analyzer"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PipelineRun:
    name: str
    duration_minutes: int
    cost_per_minute: float

class PipeCost:
    def __init__(self):
        self.runs: List[PipelineRun] = []
    
    def add_run(self, name: str, duration: int, cost_per_min: float):
        self.runs.append(PipelineRun(name, duration, cost_per_min))
    
    def get_total_cost(self) -> float:
        return sum(r.duration_minutes * r.cost_per_minute for r in self.runs)
    
    def get_cost_by_pipeline(self) -> Dict[str, float]:
        costs = {}
        for run in self.runs:
            costs[run.name] = costs.get(run.name, 0) + (run.duration_minutes * run.cost_per_minute)
        return costs
    
    def get_statistics(self) -> Dict:
        return {'total_runs': len(self.runs), 'total_cost': self.get_total_cost()}
