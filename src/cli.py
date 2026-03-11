import os
import json
import typer
import networkx as nx
import git
import shutil
import tempfile
from .orchestrator import Orchestrator

app = typer.Typer()

def is_github_url(path: str) -> bool:
    return path.startswith("https://github.com/") or path.endswith(".git")

def clone_repo(url: str) -> str:
    temp_dir = tempfile.mkdtemp(prefix="cartographer_")
    print(f"Cloning {url} into {temp_dir}...")
    git.Repo.clone_from(url, temp_dir)
    return temp_dir

@app.command(name="analyze")
def analyze(path: str = typer.Argument(".", help="Local path or GitHub URL to analyze")):
    """
    Run full analysis on the target repository.
    """
    cleanup_needed = False
    repo_path = path

    if is_github_url(path):
        repo_path = clone_repo(path)
        cleanup_needed = True

    try:
        orchestrator = Orchestrator(repo_path)
        results = orchestrator.run_analysis()
        
        print("\n--- Analysis Summary ---")
        print(f"Modules Processed: {results['module_count']}")
        print(f"Lineage Edges:      {results['lineage_edges']}")
        print("\nTop 5 PageRank Hubs:")
        for hub, score in results['top_hubs']:
            print(f"  {hub}: {score:.4f}")
            
    finally:
        if cleanup_needed and os.path.exists(repo_path):
            print(f"Cleaning up temporary directory: {repo_path}")
            import stat
            def remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(repo_path, onerror=remove_readonly)

@app.command(name="blast-radius")
def blast_radius(node_id: str):
    """
    Identify downstream blast radius of a transformation or dataset.
    """
    graph_path = ".cartography/lineage_graph.json"
    if not os.path.exists(graph_path):
        print("Lineage graph not found. Run 'analyze' first.")
        return

    with open(graph_path, "r") as f:
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
    graph_path = ".cartography/lineage_graph.json"
    if not os.path.exists(graph_path):
        print("Lineage graph not found. Run 'analyze' first.")
        return

    with open(graph_path, "r") as f:
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
