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
def analyze(
    path: str = typer.Argument(".", help="Local path or GitHub URL to analyze"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Only analyze changed files since last run")
):
    """
    Run full or incremental analysis on the target repository.
    """
    cleanup_needed = False
    repo_path = path

    if is_github_url(path):
        repo_path = clone_repo(path)
        cleanup_needed = True

    try:
        orchestrator = Orchestrator(repo_path)
        results = orchestrator.run_analysis(incremental=incremental)
        
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

@app.command(name="query")
def query_graph(question: str):
    """
    Directly query the codebase knowledge graph using the Navigator agent.
    """
    from .agents.navigator import NavigatorAgent, set_navigator_context
    from .agents.semanticist import SemanticistAgent
    from .orchestrator import Orchestrator
    
    # We need to load existing state
    # Orchestrator's repo_path is just a dummy here as we expect .cartography to exist
    orchestrator = Orchestrator(".") 
    
    graph_path = os.path.join(orchestrator.output_dir, "module_graph.json")
    if not os.path.exists(graph_path):
        print("Analysis artifacts not found. Please run 'analyze' first.")
        return
        
    print(f"Loading knowledge graph and semantic index...")
    orchestrator.kg_manager.deserialize(graph_path)
    # Lineage too
    lineage_path = os.path.join(orchestrator.output_dir, "lineage_graph.json")
    if os.path.exists(lineage_path):
        orchestrator.kg_manager.deserialize_lineage(lineage_path)
        
    semanticist = SemanticistAgent(orchestrator.repo_path)
    set_navigator_context(orchestrator.kg_manager, semanticist)
    
    navigator = NavigatorAgent()
    print(f"Navigator (GPT-OSS) Investigating: '{question}'...")
    
    response = navigator.query(question)
    print("\n--- Navigator Response ---")
    print(response)
    print("\nActions audited to .cartography/cartography_trace.jsonl")

if __name__ == "__main__":
    app()
