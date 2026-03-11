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
        return None

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        tree = parser.parse(content)
        return tree, content
    except Exception as e:
        import logging
        logging.error(f"Error parsing AST for {file_path}: {e}")
        return None, None

def extract_python_structure(tree, content: bytes):
    """
    Extracts deep structure from Python AST.
    """
    imports = []
    functions = []
    classes = []
    
    if not tree:
        return imports, functions, classes
        
    root_node = tree.root_node
    
    # Simple recursive traversal for demonstration
    # Real implementation would use S-expression queries
    def traverse(node):
        if node.type == "import_statement":
            imports.append(content[node.start_byte:node.end_byte].decode("utf8"))
        elif node.type == "import_from_statement":
            imports.append(content[node.start_byte:node.end_byte].decode("utf8"))
        elif node.type == "function_definition":
            func_name_node = node.child_by_field_name("name")
            if func_name_node:
                # Basic decorator check (rough heuristic for now)
                decorators = [content[c.start_byte:c.end_byte].decode("utf8") for c in node.children if c.type == "decorator"]
                dec_str = f" [{', '.join(decorators)}]" if decorators else ""
                functions.append(func_name_node.text.decode("utf8") + dec_str)
        elif node.type == "class_definition":
            class_name_node = node.child_by_field_name("name")
            superclasses_node = node.child_by_field_name("superclasses")
            if class_name_node:
                base_str = f"({content[superclasses_node.start_byte:superclasses_node.end_byte].decode('utf8')})" if superclasses_node else ""
                classes.append(class_name_node.text.decode("utf8") + base_str)
                
        for child in node.children:
            traverse(child)
            
    traverse(root_node)
    return imports, functions, classes

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
