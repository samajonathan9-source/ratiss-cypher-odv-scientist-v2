
# schemas.py - RATISS V9 Aeon Prime Standard Schemas
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Theory:
    name: str
    equations: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    target: str = "CPU_LOCAL"

    def __post_init__(self):
        # Support alias 'parameters' if provided
        if not self.params and getattr(self, 'parameters', None):
            self.params = getattr(self, 'parameters')

    def hash(self) -> str:
        payload = {
            "name": self.name,
            "equations": self.equations,
            "params": self.params,
            "target": self.target
        }
        raw_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_json.encode('utf-8')).hexdigest()[:16]

@dataclass
class Request:
    theory_hash: str
    code: str
    resources: Dict[str, Any]

# Alias for backward compatibility
Query = Request

@dataclass
class Result:
    theory_hash: str = ""
    data: Any = field(default_factory=dict)
    zk_commitment: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
