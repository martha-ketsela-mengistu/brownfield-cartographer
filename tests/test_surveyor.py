import pytest
from src.agents.surveyor import SurveyorAgent
from src.analyzers.tree_sitter_analyzer import analyze_ast, extract_python_structure
import os

def test_complexity_counting():
    agent = SurveyorAgent("dummy_path")
    # Mock a simple tree with one 'if_statement'
    class MockNode:
        def __init__(self, type, children=None):
            self.type = type
            self.children = children or []
    
    class MockTree:
        def __init__(self, root_node):
            self.root_node = root_node
            
    root = MockNode("module", [
        MockNode("function_definition", [
            MockNode("if_statement")
        ])
    ])
    tree = MockTree(root)
    
    complexity = agent.count_complexity(tree)
    assert complexity == 2.0 # 1 base + 1 if

def test_extract_python_structure():
    # Create a temporary python file
    content = b"import os\ndef test_func():\n    pass\nclass TestClass:\n    pass"
    with open("tmp_test.py", "wb") as f:
        f.write(content)
    
    try:
        tree, tree_content = analyze_ast("tmp_test.py")
        imports, functions, classes = extract_python_structure(tree, tree_content)
        
        assert "os" in str(imports) or "import os" in str(imports)
        assert any(f['name'] == "test_func" for f in functions)
        assert any(c['name'] == "TestClass" for c in classes)
        # Check for line ranges
        assert functions[0]['line_range'][0] == 2
    finally:
        if os.path.exists("tmp_test.py"):
            os.remove("tmp_test.py")
