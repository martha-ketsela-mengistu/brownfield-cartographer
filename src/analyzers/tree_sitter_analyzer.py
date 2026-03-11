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

    with open(file_path, "rb") as f:
        content = f.read()

    tree = parser.parse(content)
    return tree
