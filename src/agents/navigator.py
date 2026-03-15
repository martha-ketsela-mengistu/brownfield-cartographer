import os
import json
import logging
import operator
from typing import Annotated, List, Union, Dict, Any
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import networkx as nx

from ..graph.knowledge_graph import KnowledgeGraphManager
from ..agents.semanticist import IntelligentLLMWrapper
from ..utils.trace_logger import default_trace

logger = logging.getLogger(__name__)

# Global KG Manager for tools to access (in a real app, this would be passed via context)
_kg_manager: KnowledgeGraphManager = None
_semanticist: Any = None

def set_navigator_context(kg_manager: KnowledgeGraphManager, semanticist: Any):
    global _kg_manager, _semanticist
    _kg_manager = kg_manager
    _semanticist = semanticist

@tool
def find_implementation(concept: str) -> str:
    """
    Search for implementation logic or business concepts in the codebase using semantic similarity.
    Example: 'Where is the revenue calculation logic?'
    """
    if not _semanticist: return "Error: Semanticist not initialized."
    
    # Use semanticist's chroma collection
    results = _semanticist.collection.query(
        query_texts=[concept],
        n_results=5
    )
    
    formatted_results = []
    for i in range(len(results['ids'][0])):
        formatted_results.append(f"- Module: `{results['ids'][0][i]}`\n  Purpose: {results['documents'][0][i]}\n  Method: **Semantic Search (Vector Index)**")
    
    res_str = "\n".join(formatted_results)
    
    # Log action to trace
    default_trace.log_action(
        agent="Navigator",
        action="find_implementation",
        evidence=f"Semantic search for '{concept}' in ChromaDB",
        confidence=0.85,
        metadata={"concept": concept, "top_result": results['ids'][0][0] if results['ids'][0] else None}
    )
    
    return f"### Semantic Findings for '{concept}':\n{res_str}"

@tool
def trace_lineage(dataset: str, direction: str = "upstream") -> str:
    """
    Trace the data lineage for a dataset or table. 
    Direction can be 'upstream' (what produces this?) or 'downstream' (what uses this?).
    """
    if not _kg_manager: return "Error: KG Manager not initialized."
    
    edges = []
    if direction == "upstream":
        edges = _kg_manager.lineage_graph.in_edges(dataset, data=True)
    else:
        edges = _kg_manager.lineage_graph.out_edges(dataset, data=True)
        
    formatted = []
    for u, v, data in edges:
        formatted.append(f"- `{u}` -> `{v}`\n  - Via: `{data.get('type', 'link')}`\n  - Source: `{data.get('file_path', 'unknown')}`\n  - Method: **Static Lineage Analysis**")
        
    res_str = "\n".join(formatted) if formatted else f"No {direction} lineage found for `{dataset}`."
    
    # Log action to trace
    default_trace.log_action(
        agent="Navigator",
        action="trace_lineage",
        evidence=f"Graph traversal on lineage_graph (direction={direction})",
        confidence=1.0,
        metadata={"dataset": dataset, "direction": direction, "edge_count": len(edges)}
    )
    
    return f"### {direction.capitalize()} Lineage for `{dataset}`:\n{res_str}"

@tool
def blast_radius(module_path: str) -> str:
    """
    Calculate the potential impact (blast radius) of changing a specific module.
    """
    if not _kg_manager: return "Error: KG Manager not initialized."
    
    # Blast radius = downstream dependencies in both module and lineage graphs
    impacted = []
    
    # 1. Module graph (direct imports)
    if module_path in _kg_manager.graph:
        downstream = _kg_manager.graph.out_edges(module_path)
        for u, v in downstream:
            impacted.append(f"- `{v}` (Direct Import)")
            
    # 2. Lineage graph (data flow)
    # Use nx.descendants to find all transitive impacted nodes
    if module_path in _kg_manager.lineage_graph:
        transitive_impact = nx.descendants(_kg_manager.lineage_graph, module_path)
        for node in transitive_impact:
            impacted.append(f"- `{node}` (Transitive Data Dependent)")
    
    # Also check if this file is a source of any transformation
    norm_module_path = os.path.normpath(module_path)
    for u, v, data in _kg_manager.lineage_graph.edges(data=True):
        edge_path = data.get("file_path")
        if edge_path and os.path.normpath(edge_path) == norm_module_path:
            impacted.append(f"- `{v}` (Data Sink of transformation in this file)")
            # Add descendants of these sinks too
            transitive_sinks = nx.descendants(_kg_manager.lineage_graph, v)
            for node in transitive_sinks:
                impacted.append(f"- `{node}` (Transitive Data Dependent via {v})")

    res_str = "\n".join(set(impacted)) if impacted else f"No direct or transitive downstream impact detected for `{module_path}`."
    res_str += "\n\nMethod: **Graph Traversal (Descendants Analysis)**"
    
    # Log action to trace
    default_trace.log_action(
        agent="Navigator",
        action="blast_radius",
        evidence=f"Impact analysis on module and lineage graphs for {module_path}",
        confidence=0.9,
        metadata={"module_path": module_path, "impact_count": len(impacted)}
    )
    
    return f"### Blast Radius of `{module_path}`:\n{res_str}"

@tool
def explain_module(path: str) -> str:
    """
    Provides a detailed explanation of a module's purpose, structure, and position in the architecture.
    """
    if not _kg_manager: return "Error: KG Manager not initialized."
    
    # Find module node
    module = None
    for m in _kg_manager.data_store.modules:
        if m.path == path:
            module = m
            break
            
    if not module:
        return f"Module `{path}` not found in index."
        
    explanation = f"### Module: `{module.path}`\n"
    explanation += f"- **Purpose**: {module.purpose_statement}\n"
    explanation += f"- **Domain**: {module.domain_cluster}\n"
    explanation += f"- **Language**: {module.language}\n"
    explanation += f"- **Complexity**: {module.complexity_score:.2f} (Cyclomatic)\n"
    
    func_list = []
    for f in module.functions:
        rng = f.get('line_range')
        rng_str = f" [L{rng[0]}-L{rng[1]}]" if rng else ""
        func_list.append(f"`{f['name']}`{rng_str}")
    
    explanation += f"- **Functions**: {', '.join(func_list) if func_list else 'None'}\n"
    explanation += f"- **Analysis Method**: **Static Analysis + LLM Purpose Inference**\n"
    
    if module.is_doc_drift:
        explanation += f"\n> [!WARNING]\n> **Doc Drift Detected**: {module.doc_drift_explanation}\n"

    # Log action to trace
    default_trace.log_action(
        agent="Navigator",
        action="explain_module",
        evidence=f"Synthesis of indexed metadata for {path}",
        confidence=1.0,
        metadata={"path": path, "is_drift": module.is_doc_drift}
    )
    
    return explanation

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

class NavigatorAgent:
    def __init__(self, model_name: str = None):
        self.tools = [find_implementation, trace_lineage, blast_radius, explain_module]
        
        # Use bulk model designated in env, or fall back to ministral
        if not model_name:
            model_name = os.getenv("OLLAMA_MODEL_BULK", "ministral-3:8b")
            
        # Use Ollama via OpenAI-compatible endpoint
        ollama_host = os.getenv("OLLAMA_HOST", "https://ollama.com")

        self.model = ChatOllama(
            model=model_name,
            base_url=ollama_host,
        ).bind_tools(self.tools)
        
        # Build Graph
        builder = StateGraph(AgentState)
        builder.add_node("agent", self._call_model)
        builder.add_node("action", self._take_action)
        
        builder.set_entry_point("agent")
        builder.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "action",
                "end": END
            }
        )
        builder.add_edge("action", "agent")
        self.app = builder.compile()

    def _should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return "end"
        return "continue"

    def _call_model(self, state: AgentState):
        messages = state["messages"]
        response = self.model.invoke(messages)
        return {"messages": [response]}

    def _take_action(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        results = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Dispatch to actual tool functions
            tool_map = {t.name: t for t in self.tools}
            tool_fn = tool_map.get(tool_name)
            
            if tool_fn:
                result = tool_fn.invoke(tool_args)
                results.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result)
                ))
            else:
                results.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=f"Error: Tool {tool_name} not found."
                ))
                
        return {"messages": results}

    def query(self, user_input: str) -> str:
        """
        Main entry point for querying the Navigator.
        """
        logger.info(f"Navigator Query: {user_input}")
        
        inputs = {"messages": [HumanMessage(content=user_input)]}
        final_state = self.app.invoke(inputs)
        
        return final_state["messages"][-1].content
