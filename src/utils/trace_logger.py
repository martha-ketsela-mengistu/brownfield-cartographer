import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

class TraceLogger:
    def __init__(self, output_dir: str = ".cartography"):
        self.output_path = os.path.join(output_dir, "cartography_trace.jsonl")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def log_action(self, agent: str, action: str, evidence: str, confidence: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Logs an analysis action with evidence and confidence.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "evidence": evidence,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

# Global instance for easy access
default_trace = TraceLogger()
