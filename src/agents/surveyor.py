import os
import git
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..models.nodes import ModuleNode
from ..analyzers.tree_sitter_analyzer import LanguageRouter, analyze_ast
from ..utils.trace_logger import default_trace

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
        complexity = 0.0
        
        try:
            tree, content = analyze_ast(file_path)
            if tree and content:
                complexity = self.count_complexity(tree)
                
                if file_path.endswith(".py"):
                    from ..analyzers.tree_sitter_analyzer import extract_python_structure
                    # Use tree-sitter for imports (easier to find in AST)
                    imports, ts_funcs, ts_classes = extract_python_structure(tree, content)
                    
                    # Create maps for quick range lookup if TS succeeded
                    ts_func_ranges = {f['name']: f['line_range'] for f in ts_funcs}
                    ts_class_ranges = {c['name']: c['line_range'] for c in ts_classes}

                    # Use Jedi for deep semantics (signatures, docstrings)
                    import jedi
                    try:
                        script = jedi.Script(code=content.decode("utf-8"), path=file_path)
                        names = script.get_names(all_scopes=True, definitions=True)
                        
                        seen_funcs = set()
                        seen_classes = set()

                        for name in names:
                            if name.type == "function":
                                sigs = name.get_signatures()
                                sig = sigs[0].to_string() if sigs else name.name + "()"
                                
                                # Prefer TS range for full block, fallback to Jedi start line
                                rng = ts_func_ranges.get(name.name, (name.line, name.line))
                                
                                functions.append({
                                    "name": name.name,
                                    "signature": sig,
                                    "docstring": name.docstring() or None,
                                    "line_range": rng
                                })
                                seen_funcs.add(name.name)
                            elif name.type == "class":
                                rng = ts_class_ranges.get(name.name, (name.line, name.line))
                                classes.append({
                                    "name": name.name,
                                    "signature": f"class {name.name}",
                                    "docstring": name.docstring() or None,
                                    "line_range": rng
                                })
                                seen_classes.add(name.name)
                                
                        # Fill in anything TS found that Jedi missed
                        for f in ts_funcs:
                            if f['name'] not in seen_funcs:
                                functions.append({
                                    "name": f['name'],
                                    "signature": f['name'] + "()",
                                    "docstring": None,
                                    "line_range": f['line_range']
                                })
                        for c in ts_classes:
                            if c['name'] not in seen_classes:
                                classes.append({
                                    "name": c['name'],
                                    "signature": f"class {c['name']}",
                                    "docstring": None,
                                    "line_range": c['line_range']
                                })

                    except Exception as jedi_e:
                        import logging
                        logging.warning(f"Jedi failed for {file_path}: {jedi_e}")
                        # Fallback to tree-sitter
                        functions = [{"name": f['name'], "signature": f['name']+"()", "docstring": None, "line_range": f['line_range']} for f in ts_funcs]
                        classes = [{"name": c['name'], "signature": c['name'], "docstring": None, "line_range": c['line_range']} for c in ts_classes]
                        
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

        # Log action to trace
        default_trace.log_action(
            agent="Surveyor",
            action="analyze_module",
            evidence=f"AST parsing + Git log: {rel_path}",
            confidence=0.9 if tree else 0.5,
            metadata={"path": rel_path, "loc": loc, "functions": len(functions)}
        )

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
            complexity_score=complexity,
            is_dead_code_candidate=False, # Set later by orchestrator
        )

    def count_complexity(self, tree) -> float:
        """
        Estimates cyclomatic complexity by counting decision nodes in the AST.
        """
        if not tree:
            return 0.0
            
        decision_nodes = {
            # Python
            "if_statement", "for_statement", "while_statement", "except_clause", "with_statement", "conditional_expression",
            # SQL
            "where_clause", "join_clause", "case_expression",
        }
        
        count = 1.0 # Base complexity
        
        def traverse(node):
            nonlocal count
            if node.type in decision_nodes:
                count += 1.0
            for child in node.children:
                traverse(child)
                
        traverse(tree.root_node)
        return count

    def get_git_velocity(self, rel_path: str, days: int = 90) -> int:
        if not self.repo:
            return 0
        
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        try:
            commits = list(self.repo.iter_commits(paths=rel_path, since=since_date))
            return len(commits)
        except Exception:
            return 0
