import os
import json
import logging
import hashlib
import networkx as nx
from typing import Dict, Any
from .agents.surveyor import SurveyorAgent
from .agents.hydrologist import HydrologistAgent
from .graph.knowledge_graph import KnowledgeGraphManager
from .graph.visualizer import GraphVisualizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, repo_path: str, base_output_dir: str = ".cartography"):
        self.repo_path = os.path.abspath(repo_path)
        
        # Generate a unique project ID based on the repo name and path
        repo_name = os.path.basename(self.repo_path) or "unknown_repo"
        path_hash = hashlib.md5(self.repo_path.encode()).hexdigest()[:8]
        self.output_dir = os.path.join(base_output_dir, f"{repo_name}_{path_hash}")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self._setup_logging()
        self.kg_manager = KnowledgeGraphManager()

    def _setup_logging(self):
        log_file = os.path.join(self.output_dir, "analysis.log")
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
        
    def run_analysis(self, incremental: bool = False):
        logger.info(f"Starting {'incremental ' if incremental else 'full '}analysis for: {self.repo_path}")
        
        last_commit = None
        meta_path = os.path.join(self.output_dir, "meta.json")
        
        if incremental:
            # 0. Load existing state
            if os.path.exists(os.path.join(self.output_dir, "module_graph.json")):
                logger.info("Loading existing knowledge graph for incremental update...")
                self.kg_manager.deserialize(os.path.join(self.output_dir, "module_graph.json"))
                if os.path.exists(os.path.join(self.output_dir, "lineage_graph.json")):
                    self.kg_manager.deserialize_lineage(os.path.join(self.output_dir, "lineage_graph.json"))
            
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    last_commit = meta.get("last_commit")
            
            if not last_commit:
                logger.warning("No previous commit found. Falling back to full analysis.")
                incremental = False

        # Determine files to analyze
        target_files = []
        if incremental and last_commit:
            try:
                import git
                repo = git.Repo(self.repo_path)
                changed_files = repo.git.diff('--name-only', last_commit, 'HEAD').splitlines()
                target_files = [os.path.join(self.repo_path, f) for f in changed_files if f.endswith((".py", ".sql", ".yaml", ".yml"))]
                logger.info(f"Incremental mode: detected {len(target_files)} changed files.")
            except Exception as e:
                logger.error(f"Failed to get git diff: {e}. Falling back to full analysis.")
                incremental = False

        if not incremental:
            # Full walk
            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", self.output_dir, ".antigravity", ".specify"]]
                for file in files:
                    if file.endswith((".py", ".sql", ".yaml", ".yml")):
                        target_files.append(os.path.join(root, file))

        # 1. Surveyor (Static Structure)
        logger.info(f"Phase 1: Running Surveyor on {len(target_files)} files...")
        surveyor = SurveyorAgent(self.repo_path)
        module_count = 0
        
        for file_path in target_files:
            if not os.path.exists(file_path): continue # File might have been deleted
            try:
                node = surveyor.analyze_module(file_path)
                self.kg_manager.add_module(node)
                module_count += 1
            except Exception as e:
                logger.error(f"Failed to analyze module {file_path}: {e}")
        
        logger.info(f"Surveyor finished. Processed {module_count} modules.")

        # 2. Hydrologist (Data Lineage)
        # (Always re-run lineage as it's cheap and global)
        logger.info("Phase 2: Running Hydrologist...")
        try:
            hydrologist = HydrologistAgent(self.repo_path, self.kg_manager)
            hydrologist.analyze_lineage()
        except Exception as e:
            logger.error(f"Hydrologist failed: {e}")
            
        logger.info(f"Hydrologist finished. Lineage graph has {len(self.kg_manager.lineage_graph.edges)} edges.")

        # 3. Semanticist (Deep Analysis)
        logger.info("Phase 3: Running Semanticist...")
        try:
            from .agents.semanticist import SemanticistAgent
            semanticist = SemanticistAgent(self.repo_path)
            
            # For incremental, we only need to regenerate purpose for changed files
            # BUT for clustering we need all modules.
            modules_to_analyze = [m for m in self.kg_manager.data_store.modules if os.path.join(self.repo_path, m.path) in target_files] if incremental else self.kg_manager.data_store.modules

            for node in modules_to_analyze:
                full_path = os.path.join(self.repo_path, node.path)
                logger.info(f"Generating purpose for {node.path}...")
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                result = semanticist.generate_purpose_statement(node, content)
                node.purpose_statement = result.purpose_statement
                node.is_doc_drift = result.is_doc_drift
                node.doc_drift_explanation = result.doc_drift_explanation
                
                # Immediately update the graph node
                if node.id in self.kg_manager.graph:
                    self.kg_manager.graph.nodes[node.id]['purpose_statement'] = node.purpose_statement
                    self.kg_manager.graph.nodes[node.id]['is_doc_drift'] = node.is_doc_drift
                    self.kg_manager.graph.nodes[node.id]['doc_drift_explanation'] = node.doc_drift_explanation
                
                if result.is_doc_drift:
                    logger.warning(f"Doc Drift detected in {node.path}: {result.doc_drift_explanation}")
            
            # Cluster with refined boundaries (Always re-cluster for global consistency)
            logger.info("Identifying Business Domain boundaries...")
            try:
                domain_map = semanticist.cluster_into_domains()
                for node in self.kg_manager.data_store.modules:
                    node.domain_cluster = domain_map.get(node.id, "Uncategorized")
                    if node.id in self.kg_manager.graph:
                        self.kg_manager.graph.nodes[node.id]['domain_cluster'] = node.domain_cluster
            except Exception as cluster_error:
                logger.error(f"Clustering failed: {cluster_error}")

            # 4: Archivist (Central Synthesis Hub)
            logger.info("Phase 4: Running Archivist for Central Synthesis...")
            try:
                from .agents.archivist import ArchivistAgent
                archivist = ArchivistAgent(self.repo_path, self.kg_manager)
                
                # Synthesis 1: CODEBASE.md
                codebase_md = archivist.generate_CODEBASE_md()
                codebase_path = os.path.join(self.output_dir, "CODEBASE.md")
                with open(codebase_path, "w", encoding="utf-8") as f:
                    f.write(codebase_md)
                logger.info(f"CODEBASE.md saved to {codebase_path}")
                
                # Synthesis 2: Onboarding Brief
                onboarding_brief = archivist.generate_onboarding_brief()
                brief_path = os.path.join(self.output_dir, "onboarding_brief.md")
                with open(brief_path, "w", encoding="utf-8") as f:
                    f.write(onboarding_brief)
                logger.info(f"Onboarding brief saved to {brief_path}")
                
            except Exception as arch_error:
                logger.error(f"Archivist failed: {arch_error}")

        except Exception as e:
            logger.error(f"Semanticist failed: {e}")

        # 5. Computing Metrics
        logger.info("Computing graph metrics...")
        pagerank = self.kg_manager.compute_pagerank()
        
        # 6. Dead Code Detection
        logger.info("Detecting dead code candidates...")
        try:
            imported_modules = set()
            for u, v, data in self.kg_manager.graph.edges(data=True):
                if data.get("type") == "IMPORTS":
                    imported_modules.add(v)
            
            for node in self.kg_manager.data_store.modules:
                # If a module is NOT imported by anyone else, it might be dead code
                # (Excluding known entry points or modules with no exports if they are scripts)
                if node.id not in imported_modules:
                    node.is_dead_code_candidate = True
                    if node.id in self.kg_manager.graph:
                        self.kg_manager.graph.nodes[node.id]['is_dead_code_candidate'] = True
                    logger.info(f"Dead code candidate detected: {node.path}")
        except Exception as e:
            logger.error(f"Dead code detection failed: {e}")
        
        # 7. Serialization
        logger.info(f"Saving artifacts to {self.output_dir}")
        self.kg_manager.serialize(os.path.join(self.output_dir, "module_graph.json"))
        self.kg_manager.serialize_lineage(os.path.join(self.output_dir, "lineage_graph.json"))
        
        # Save current commit for next run
        try:
            import git
            repo = git.Repo(self.repo_path)
            current_commit = repo.head.commit.hexsha
            with open(meta_path, "w") as f:
                json.dump({"last_commit": current_commit}, f)
        except:
            pass
        
        # 8. Visualization
        logger.info("Generating visualizations...")
        viz_dir = os.path.join(self.output_dir, "visualizations")
        if not os.path.exists(viz_dir):
            os.makedirs(viz_dir)
        GraphVisualizer.visualize_graph(self.kg_manager.graph, os.path.join(viz_dir, "module_graph.html"), "Module Graph")
        GraphVisualizer.visualize_graph(self.kg_manager.lineage_graph, os.path.join(viz_dir, "lineage_graph.html"), "Lineage Graph")
        
        logger.info("Analysis complete.")
        return {
            "module_count": len(self.kg_manager.data_store.modules),
            "lineage_edges": len(self.kg_manager.lineage_graph.edges),
            "top_hubs": sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        }
