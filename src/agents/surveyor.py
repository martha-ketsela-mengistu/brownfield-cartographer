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
                    # Use tree-sitter for imports (easier to find in AST)
                    imports, _, _ = extract_python_structure(tree, content)
                    
                    # Use Jedi for deep semantics (signatures, docstrings)
                    import jedi
                    try:
                        script = jedi.Script(code=content.decode("utf-8"), path=file_path)
                        names = script.get_names(all_scopes=True, definitions=True)
                        
                        for name in names:
                            if name.type == "function":
                                sigs = name.get_signatures()
                                sig = sigs[0].to_string() if sigs else name.name + "()"
                                functions.append({
                                    "name": name.name,
                                    "signature": sig,
                                    "docstring": name.docstring() or None
                                })
                            elif name.type == "class":
                                classes.append({
                                    "name": name.name,
                                    "signature": f"class {name.name}",
                                    "docstring": name.docstring() or None
                                })
                    except Exception as jedi_e:
                        import logging
                        logging.warning(f"Jedi failed for {file_path}: {jedi_e}")
                        # Fallback to tree-sitter for names if Jedi fails
                        _, ts_funcs, ts_classes = extract_python_structure(tree, content)
                        functions = [{"name": f, "signature": f, "docstring": None} for f in ts_funcs]
                        classes = [{"name": c, "signature": c, "docstring": None} for c in ts_classes]
                        
                elif file_path.endswith(".sql"):
                    from ..analyzers.tree_sitter_analyzer import extract_sql_structure
                    tables, queries = extract_sql_structure(tree, content)
                    imports = [f"table={t}" for t in tables]
                    functions = [{"name": q, "signature": q, "docstring": None} for q in queries]
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
