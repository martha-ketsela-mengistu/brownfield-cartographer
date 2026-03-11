import re
from typing import List, Dict, Any

class PythonDataFlowAnalyzer:
    def __init__(self):
        # Patterns for common data operations
        self.patterns = {
            "pandas_read": re.compile(r"pd\.read_(csv|parquet|sql|table|excel|json)\((.*?)\)"),
            "pandas_write": re.compile(r"\.to_(csv|parquet|sql|json)\((.*?)\)"),
            "spark_read": re.compile(r"spark\.read\.(csv|parquet|table|json)\((.*?)\)"),
            "spark_write": re.compile(r"\.write\.(csv|parquet|table|json)\((.*?)\)"),
            "sql_execute": re.compile(r"\.execute\((.*?)\)"),
        }

    def analyze_content(self, content: str) -> Dict[str, List[str]]:
        """
        Analyzes Python code content for data flow patterns.
        Returns a dict with 'sources' and 'targets' keys.
        """
        sources = set()
        targets = set()

        for key, pattern in self.patterns.items():
            for match in pattern.finditer(content):
                arg_content = match.group(2).strip()
                
                # Simple extraction: if it's a string literal, get the content
                # Otherwise, log as 'dynamic'
                extracted_name = "dynamic"
                if arg_content.startswith(("'", '"')):
                    # Very simple string extraction
                    extracted_name = arg_content.strip("'\"").split(",")[0].strip("'\"")
                
                if "read" in key or "execute" in key:
                    sources.add(extracted_name)
                elif "write" in key:
                    targets.add(extracted_name)

        return {
            "sources": list(sources),
            "targets": list(targets)
        }
