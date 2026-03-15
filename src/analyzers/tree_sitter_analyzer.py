import os
try:
    import tree_sitter_python as tspython
except ImportError:
    tspython = None

try:
    import tree_sitter_sql as tssql
except ImportError:
    tssql = None

try:
    import tree_sitter_yaml as tsyaml
except ImportError:
    tsyaml = None

from tree_sitter import Language, Parser

class LanguageRouter:
    def __init__(self):
        self.languages = {}
        if tspython:
            self.languages[".py"] = Language(tspython.language())
        if tssql:
            self.languages[".sql"] = Language(tssql.language())
        if tsyaml:
            self.languages[".yaml"] = Language(tsyaml.language())
            self.languages[".yml"] = Language(tsyaml.language())
            
        self.parsers = {ext: Parser(lang) for ext, lang in self.languages.items()}

    def get_parser(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        return self.parsers.get(ext)

    def get_language(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        return self.languages.get(ext)

def analyze_ast(file_path: str):
    router = LanguageRouter()
    parser = router.get_parser(file_path)
    if not parser:
        return None, None

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        tree = parser.parse(content)
        return tree, content
    except Exception as e:
        import logging
        logging.error(f"Error parsing AST for {file_path}: {e}")
        return None, None

from tree_sitter import Language, Parser, Query, QueryCursor
# S-expression queries for reliable structural extraction
PY_QUERY = """
(import_statement (dotted_name) @import)
(import_from_statement (dotted_name) @import_from)
(function_definition name: (identifier) @function) @function_full
(class_definition name: (identifier) @class) @class_full
"""

def extract_python_structure(tree, content: bytes):
    """
    Extracts deep structure from Python AST using S-expression queries.
    Captures names and line ranges.
    """
    if not tree or not tspython:
        return [], [], []
        
    language = Language(tspython.language())
    query = Query(language, PY_QUERY)
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)
    
    # captures is a dict mapping tag -> list of nodes
    imports = []
    # Store functions/classes as dicts with metadata
    functions = []
    classes = []
    
    # We need to pair @function with its @function_full to get the name vs the whole block
    # However, captures() in 0.25+ returns a dict. Let's see how pairings work.
    # Actually, it might be easier to use matches() if we need pairings, 
    # but let's look at the dictionary contents.
    
    if "import" in captures:
        for node in captures["import"]:
            imports.append(content[node.start_byte:node.end_byte].decode("utf8", errors="ignore"))
    if "import_from" in captures:
        for node in captures["import_from"]:
            imports.append(content[node.start_byte:node.end_byte].decode("utf8", errors="ignore"))
            
    # For functions and classes, we'll use a simpler approach since dict keys lose ordering/pairing
    # Re-run for specific pairs if needed, or just use the node's own children.
    # Actually, the 'function' identifier is a child of 'function_definition'.
    
    if "function_full" in captures:
        for node in captures["function_full"]:
            name_node = node.child_by_field_name("name")
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte].decode("utf8", errors="ignore")
                functions.append({
                    "name": name,
                    "line_range": (node.start_point[0] + 1, node.end_point[0] + 1)
                })
                
    if "class_full" in captures:
        for node in captures["class_full"]:
            name_node = node.child_by_field_name("name")
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte].decode("utf8", errors="ignore")
                classes.append({
                    "name": name,
                    "line_range": (node.start_point[0] + 1, node.end_point[0] + 1)
                })
            
    return list(set(imports)), functions, classes

def extract_sql_structure(tree, content: bytes):
    """
    Extracts table references and query structures from SQL AST.
    """
    tables = set()
    queries = []
    
    if not tree:
        return list(tables), queries
        
    def traverse(node):
        # Tree-sitter SQL grammar has specific nodes for statements
        if getattr(node, "type", "").endswith("statement"):
            queries.append(node.type)
            
        # Very rough heuristic to find table identifiers in FROM/JOIN clauses
        # The exact node types depend heavily on the tree-sitter-sql version
        if node.type == "table_reference" or node.type == "identifier":
            # Sometimes we just grab all identifiers as potential tables if they are under a FROM clause
            # For simplicity, let's just grab table_reference
            tables.add(content[node.start_byte:node.end_byte].decode("utf8"))
            
        for child in node.children:
            traverse(child)
            
    traverse(tree.root_node)
    return list(tables), queries

def extract_yaml_structure(tree, content: bytes):
    """
    Extracts key hierarchies from YAML config AST.
    """
    keys = []
    
    if not tree:
        return keys
        
    def traverse(node):
        if node.type == "block_mapping_pair":
            key_node = node.child_by_field_name("key")
            if key_node:
                keys.append(content[key_node.start_byte:key_node.end_byte].decode("utf8"))
        
        for child in node.children:
            traverse(child)
            
    traverse(tree.root_node)
    return keys
