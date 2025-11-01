"""AutoGenAPI - Auto-generate API docs from traffic patterns"""
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class APIEndpoint:
    path: str
    method: str
    request_count: int = 0
    request_samples: List[Dict] = field(default_factory=list)
    response_samples: List[Dict] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

class AutoGenAPI:
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
    
    def record_request(self, method: str, path: str, request_body: Any = None, 
                      response_body: Any = None, status_code: int = 200):
        key = f"{method}:{path}"
        if key not in self.endpoints:
            self.endpoints[key] = APIEndpoint(path=path, method=method)
        
        endpoint = self.endpoints[key]
        endpoint.request_count += 1
        endpoint.status_codes[status_code] += 1
        
        if request_body and len(endpoint.request_samples) < 3:
            endpoint.request_samples.append(request_body)
        if response_body and len(endpoint.response_samples) < 3:
            endpoint.response_samples.append(response_body)
    
    def generate_markdown(self) -> str:
        lines = ["# API Documentation\n"]
        for key, endpoint in sorted(self.endpoints.items()):
            lines.append(f"## {endpoint.method} {endpoint.path}\n")
            lines.append(f"**Requests:** {endpoint.request_count}\n")
            if endpoint.request_samples:
                lines.append("**Request Example:**\n```json")
                lines.append(str(endpoint.request_samples[0]))
                lines.append("```\n")
            if endpoint.response_samples:
                lines.append("**Response Example:**\n```json")
                lines.append(str(endpoint.response_samples[0]))
                lines.append("```\n")
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_endpoints': len(self.endpoints),
            'total_requests': sum(e.request_count for e in self.endpoints.values())
        }
