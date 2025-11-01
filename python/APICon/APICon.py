"""APICon - API Contract Testing"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class Contract:
    endpoint: str
    method: str
    request_schema: Dict
    response_schema: Dict

class APICon:
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
    
    def add_contract(self, endpoint: str, method: str, req_schema: Dict, resp_schema: Dict):
        key = f"{method}:{endpoint}"
        self.contracts[key] = Contract(endpoint, method, req_schema, resp_schema)
    
    def validate_request(self, endpoint: str, method: str, data: Dict) -> bool:
        key = f"{method}:{endpoint}"
        contract = self.contracts.get(key)
        if not contract:
            return False
        
        required = contract.request_schema.get('required', [])
        return all(field in data for field in required)
    
    def get_statistics(self) -> Dict:
        return {'total_contracts': len(self.contracts)}
