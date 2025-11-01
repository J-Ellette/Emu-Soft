"""ArchDecRec - Architecture Decision Record (ADR) template system"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ADR:
    number: int
    title: str
    status: str  # 'proposed', 'accepted', 'rejected', 'deprecated'
    context: str
    decision: str
    consequences: str
    date: str
    author: Optional[str] = None

class ArchDecRec:
    def __init__(self):
        self.adrs: List[ADR] = []
        self.next_number = 1
    
    def create_adr(self, title: str, context: str, decision: str, 
                   consequences: str, author: str = None) -> int:
        adr = ADR(
            number=self.next_number,
            title=title,
            status='proposed',
            context=context,
            decision=decision,
            consequences=consequences,
            date=datetime.utcnow().isoformat(),
            author=author
        )
        self.adrs.append(adr)
        self.next_number += 1
        return adr.number
    
    def get_adr(self, number: int) -> Optional[ADR]:
        for adr in self.adrs:
            if adr.number == number:
                return adr
        return None
    
    def update_status(self, number: int, status: str) -> bool:
        adr = self.get_adr(number)
        if adr:
            adr.status = status
            return True
        return False
    
    def generate_markdown(self, number: int) -> str:
        adr = self.get_adr(number)
        if not adr:
            return ""
        
        lines = [
            f"# ADR {adr.number}: {adr.title}\n",
            f"**Status:** {adr.status}\n",
            f"**Date:** {adr.date}\n",
            "## Context\n",
            adr.context + "\n",
            "## Decision\n",
            adr.decision + "\n",
            "## Consequences\n",
            adr.consequences + "\n"
        ]
        return "\n".join(lines)
    
    def list_adrs(self, status: Optional[str] = None) -> List[ADR]:
        if status:
            return [adr for adr in self.adrs if adr.status == status]
        return self.adrs
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_adrs': len(self.adrs),
            'by_status': {
                status: len([a for a in self.adrs if a.status == status])
                for status in ['proposed', 'accepted', 'rejected', 'deprecated']
            }
        }
