"""FlakyTest - Flaky Test Detector"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TestResult:
    test_name: str
    passed: bool
    run_number: int

class FlakyTest:
    def __init__(self):
        self.results: Dict[str, List[TestResult]] = {}
    
    def record_result(self, test_name: str, passed: bool, run_num: int):
        if test_name not in self.results:
            self.results[test_name] = []
        self.results[test_name].append(TestResult(test_name, passed, run_num))
    
    def detect_flaky(self, threshold: float = 0.2) -> List[str]:
        flaky = []
        for test_name, results in self.results.items():
            if len(results) < 2:
                continue
            
            passes = sum(1 for r in results if r.passed)
            fail_rate = 1 - (passes / len(results))
            
            if 0 < fail_rate < (1 - threshold):
                flaky.append(test_name)
        
        return flaky
    
    def get_statistics(self) -> Dict:
        return {'total_tests': len(self.results)}
