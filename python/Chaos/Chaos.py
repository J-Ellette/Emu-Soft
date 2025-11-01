"""Chaos - Chaos Engineering Scenarios"""
from typing import List, Dict, Callable
from dataclasses import dataclass

@dataclass
class ChaosScenario:
    name: str
    description: str
    action: Callable
    probability: float = 0.1

class Chaos:
    def __init__(self):
        self.scenarios: Dict[str, ChaosScenario] = {}
        self.enabled = False
    
    def add_scenario(self, name: str, desc: str, action: Callable, prob: float = 0.1):
        self.scenarios[name] = ChaosScenario(name, desc, action, prob)
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
    
    def inject_chaos(self, scenario_name: str) -> bool:
        if not self.enabled:
            return False
        
        scenario = self.scenarios.get(scenario_name)
        if scenario:
            import random
            if random.random() < scenario.probability:
                scenario.action()
                return True
        return False
    
    def get_statistics(self) -> Dict:
        return {'total_scenarios': len(self.scenarios), 'enabled': self.enabled}
