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
        self.kg_manager = KnowledgeGraphManager()
        
    def run_analysis(self):
        logger.info(f"Starting analysis for: {self.repo_path}")
        
        # 1. Surveyor (Static Structure)
        logger.info("Phase 1: Running Surveyor...")
        surveyor = SurveyorAgent(self.repo_path)
        module_count = 0
        
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
        GraphVisualizer.visualize_graph(self.kg_manager.graph, os.path.join(viz_dir, "module_graph.html"), "Module Graph")
        GraphVisualizer.visualize_graph(self.kg_manager.lineage_graph, os.path.join(viz_dir, "lineage_graph.html"), "Lineage Graph")
        
        logger.info("Analysis complete.")
        return {
            "module_count": module_count,
            "lineage_edges": len(self.kg_manager.lineage_graph.edges),
            "top_hubs": sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        }
