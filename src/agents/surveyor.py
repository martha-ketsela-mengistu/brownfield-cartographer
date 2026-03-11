import os
import git
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..models.nodes import ModuleNode
from ..analyzers.tree_sitter_analyzer import LanguageRouter, analyze_ast

class SurveyorAgent:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.router = LanguageRouter()
        try:
            self.repo = git.Repo(repo_path)
        except Exception:
            self.repo = None

    def analyze_module(self, file_path: str) -> ModuleNode:
        rel_path = os.path.relpath(file_path, self.repo_path)
        
        # Basic metrics
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        loc = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith("#") or line.strip().startswith("--"))
        comment_ratio = comment_lines / loc if loc > 0 else 0.0
        
        # Git velocity
        change_frequency = self.get_git_velocity(rel_path)
        
        # AST analysis (placeholders for now)
        imports = []
        functions = []
        classes = []
        
        # Simple heuristic extraction for now to fulfill the model
        if file_path.endswith(".py"):
            for line in lines:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
                elif line.startswith("def "):
                    functions.append(line.split("(")[0].replace("def ", ""))
                elif line.startswith("class "):
                    classes.append(line.split("(")[0].replace("class ", "").replace(":", ""))

        return ModuleNode(
            id=rel_path,
            path=rel_path,
            language=os.path.splitext(file_path)[1],
            loc=loc,
            comment_ratio=comment_ratio,
            change_frequency=change_frequency,
            imports=imports,
            functions=functions,
            classes=classes,
            complexity_score=0.0, # Placeholder
        )

    def get_git_velocity(self, rel_path: str, days: int = 30) -> int:
        if not self.repo:
            return 0
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        try:
            commits = list(self.repo.iter_commits(paths=rel_path, since=since_date))
            return len(commits)
        except Exception:
            return 0
