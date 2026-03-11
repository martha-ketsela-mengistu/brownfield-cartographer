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
        
        # AST analysis
        imports = []
        functions = []
        classes = []
        
        try:
            tree, content = analyze_ast(file_path)
            if tree and content:
                if file_path.endswith(".py"):
                    from ..analyzers.tree_sitter_analyzer import extract_python_structure
                    imports, functions, classes = extract_python_structure(tree, content)
                elif file_path.endswith(".sql"):
                    from ..analyzers.tree_sitter_analyzer import extract_sql_structure
                    tables, queries = extract_sql_structure(tree, content)
                    # For SQL, we might store these in imports/functions just to reuse the schema
                    imports = [f"table={t}" for t in tables]
                    functions = queries
                elif file_path.endswith((".yaml", ".yml")):
                    from ..analyzers.tree_sitter_analyzer import extract_yaml_structure
                    keys = extract_yaml_structure(tree, content)
                    imports = [f"key={k}" for k in keys]
        except Exception as e:
            import logging
            logging.error(f"Surveyor AST extraction failed for {file_path}: {e}")

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
