from pyvis.network import Network
import networkx as nx
import os

class GraphVisualizer:
    @staticmethod
    def visualize_graph(graph: nx.Graph, output_file: str, title: str = "Knowledge Graph"):
        """
        Generates an interactive HTML visualization using pyvis.
        """
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=isinstance(graph, nx.DiGraph))
        
        # Load the NetworkX graph
        net.from_nx(graph)
        
        # Customize nodes based on attributes if they exist
        for node in net.nodes:
            # Add some basic styling
            node["label"] = node["id"]
            node["title"] = f"Type: {node.get('type', 'Unknown')}"
            
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        net.write_html(output_file)
        print(f"Visualization saved to {output_file}")
