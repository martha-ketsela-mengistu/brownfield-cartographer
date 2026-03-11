import os
import json
import typer
import networkx as nx
from .agents.surveyor import SurveyorAgent
from .graph.knowledge_graph import KnowledgeGraphManager
from .agents.hydrologist import HydrologistAgent
from .graph.visualizer import GraphVisualizer

app = typer.Typer()

@app.command(name="analyze")
def analyze(repo_path: str = typer.Argument(".")):
    """
    Run full analysis on the target repository.
    """
    abs_repo_path = os.path.abspath(repo_path)
    print(f"Analyzing repository: {abs_repo_path}")
    
    kg_manager = KnowledgeGraphManager()
    
    # 1. Surveyor (Static Structure)
    print("\n--- Phase 1: Surveyor (Static Structure) ---")
    surveyor = SurveyorAgent(abs_repo_path)
    count = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", ".cartography", ".antigravity", ".specify"]]
        for file in files:
            if file.endswith((".py", ".sql", ".yaml", ".yml")):
                file_path = os.path.join(root, file)
                node = surveyor.analyze_module(file_path)
                kg_manager.add_module(node)
                count += 1
    print(f"Processed {count} modules.")

    # 2. Hydrologist (Data Lineage)
    print("\n--- Phase 2: Hydrologist (Data Lineage) ---")
    hydrologist = HydrologistAgent(abs_repo_path, kg_manager)
    hydrologist.analyze_lineage()
    print(f"Lineage graph built with {len(kg_manager.lineage_graph.edges)} edges.")

    # Compute PageRank
    print("\nComputing PageRank...")
    pagerank = kg_manager.compute_pagerank()
    sorted_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 5 PageRank Hubs:")
    for path, score in sorted_pr[:5]:
        print(f"  {path}: {score:.4f}")

    # Serialize
    kg_manager.serialize(".cartography/module_graph.json")
    kg_manager.serialize_lineage(".cartography/lineage_graph.json")
    print("\nSerialized graphs to .cartography/")

    # Visualize
    print("\nGenerating visualizations...")
    GraphVisualizer.visualize_graph(kg_manager.graph, ".cartography/visualizations/module_graph.html", "Module Graph")
    GraphVisualizer.visualize_graph(kg_manager.lineage_graph, ".cartography/visualizations/lineage_graph.html", "Lineage Graph")

@app.command(name="blast-radius")
def blast_radius(node_id: str):
    """
    Identify downstream blast radius of a transformation or dataset.
    """
    if not os.path.exists(".cartography/lineage_graph.json"):
        print("Lineage graph not found. Run 'analyze' first.")
        return

    with open(".cartography/lineage_graph.json", "r") as f:
        data = json.load(f)
    graph = nx.node_link_graph(data)
    
    if node_id not in graph:
        print(f"Node {node_id} not found in lineage graph.")
        return
        
    downstream = nx.descendants(graph, node_id)
    print(f"\nBlast Radius for {node_id}:")
    for d in downstream:
        print(f"  -> {d}")

@app.command(name="lineage")
def trace_lineage(dataset: str):
    """
    Trace upstream sources for a dataset.
    """
    if not os.path.exists(".cartography/lineage_graph.json"):
        print("Lineage graph not found. Run 'analyze' first.")
        return

    with open(".cartography/lineage_graph.json", "r") as f:
        data = json.load(f)
    graph = nx.node_link_graph(data)
    
    if dataset not in graph:
        print(f"Dataset {dataset} not found in lineage graph.")
        return
        
    upstream = nx.ancestors(graph, dataset)
    print(f"\nUpstream Sources for {dataset}:")
    for u in upstream:
        print(f"  <- {u}")

@app.command(name="query")
def query(question: str):
    """
    Query the codebase (Phase 4 Navigator).
    """
    print(f"Querying: {question}")
    print("Navigator not implemented yet.")

if __name__ == "__main__":
    app()
