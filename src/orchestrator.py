import os
import json
import logging
from typing import Dict, Any
from .agents.surveyor import SurveyorAgent
from .agents.hydrologist import HydrologistAgent
from .graph.knowledge_graph import KnowledgeGraphManager
from .graph.visualizer import GraphVisualizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, repo_path: str, output_dir: str = ".cartography"):
        self.repo_path = os.path.abspath(repo_path)
        self.output_dir = output_dir
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
        
    def run_analysis(self):
        logger.info(f"Starting analysis for: {self.repo_path}")
        
        # 1. Surveyor (Static Structure)
        logger.info("Phase 1: Running Surveyor...")
        surveyor = SurveyorAgent(self.repo_path)
        module_count = 0
        
        # We walk once to collect files, then process them
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", self.output_dir, ".antigravity", ".specify"]]
            for file in files:
                if file.endswith((".py", ".sql", ".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    try:
                        node = surveyor.analyze_module(file_path)
                        self.kg_manager.add_module(node)
                        module_count += 1
                    except Exception as e:
                        logger.error(f"Failed to analyze module {file_path}: {e}")
        
        logger.info(f"Surveyor finished. Processed {module_count} modules.")

        # 2. Hydrologist (Data Lineage)
        logger.info("Phase 2: Running Hydrologist...")
        try:
            hydrologist = HydrologistAgent(self.repo_path, self.kg_manager)
            hydrologist.analyze_lineage()
        except Exception as e:
            logger.error(f"Hydrologist failed: {e}")
            
        logger.info(f"Hydrologist finished. Lineage graph has {len(self.kg_manager.lineage_graph.edges)} edges.")

        # 2.5 Semanticist (Deep Analysis)
        logger.info("Phase 2.5: Running Semanticist...")
        try:
            from .agents.semanticist import SemanticistAgent
            semanticist = SemanticistAgent(self.repo_path)
            
            for node in self.kg_manager.data_store.modules:
                full_path = os.path.join(self.repo_path, node.path)
                logger.info(f"Generating purpose for {node.path}...")
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                result = semanticist.generate_purpose_statement(node, content)
                node.purpose_statement = result.purpose_statement
                node.is_doc_drift = result.is_doc_drift
                node.doc_drift_explanation = result.doc_drift_explanation
                
                # Immediately update the graph node to persist the purpose
                if node.id in self.kg_manager.graph:
                    self.kg_manager.graph.nodes[node.id]['purpose_statement'] = node.purpose_statement
                    self.kg_manager.graph.nodes[node.id]['is_doc_drift'] = node.is_doc_drift
                    self.kg_manager.graph.nodes[node.id]['doc_drift_explanation'] = node.doc_drift_explanation
                
                if result.is_doc_drift:
                    logger.warning(f"Doc Drift detected in {node.path}: {result.doc_drift_explanation}")
            
            # Cluster with refined boundaries
            logger.info("Identifying Business Domain boundaries...")
            try:
                domain_map = semanticist.cluster_into_domains()
                for node in self.kg_manager.data_store.modules:
                    node.domain_cluster = domain_map.get(node.id, "Uncategorized")
                    if node.id in self.kg_manager.graph:
                        self.kg_manager.graph.nodes[node.id]['domain_cluster'] = node.domain_cluster
            except Exception as cluster_error:
                logger.error(f"Clustering failed: {cluster_error}")

            # Synthesis: Five FDE Day-One Answers
            logger.info("Synthesizing Five FDE Day-One Answers...")
            try:
                onboarding_brief = semanticist.generate_day_one_brief(self.kg_manager)
                brief_path = os.path.join(self.output_dir, "onboarding_brief.md")
                with open(brief_path, "w", encoding="utf-8") as f:
                    f.write(onboarding_brief)
                logger.info(f"Onboarding brief saved to {brief_path}")
            except Exception as synth_error:
                logger.error(f"Synthesis failed: {synth_error}")

        except Exception as e:
            logger.error(f"Semanticist failed: {e}")

        # 3. Computing Metrics
        logger.info("Computing graph metrics...")
        pagerank = self.kg_manager.compute_pagerank()
        
        # 4. Serialization
        logger.info(f"Saving artifacts to {self.output_dir}")
        self.kg_manager.serialize(os.path.join(self.output_dir, "module_graph.json"))
        self.kg_manager.serialize_lineage(os.path.join(self.output_dir, "lineage_graph.json"))
        
        # 5. Visualization
        logger.info("Generating visualizations...")
        viz_dir = os.path.join(self.output_dir, "visualizations")
        if not os.path.exists(viz_dir):
            os.makedirs(viz_dir)
        GraphVisualizer.visualize_graph(self.kg_manager.graph, os.path.join(viz_dir, "module_graph.html"), "Module Graph")
        GraphVisualizer.visualize_graph(self.kg_manager.lineage_graph, os.path.join(viz_dir, "lineage_graph.html"), "Lineage Graph")
        
        logger.info("Analysis complete.")
        return {
            "module_count": module_count,
            "lineage_edges": len(self.kg_manager.lineage_graph.edges),
            "top_hubs": sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        }
