import os
import re
import logging
import ollama
import chromadb
import numpy as np
import tiktoken
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from ..models.nodes import ModuleNode
from ..models.semantic import ContextWindowBudget, SemanticAnalysisResult
from ..utils.trace_logger import default_trace

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

class IntelligentLLMWrapper:
    def __init__(self, model_bulk: str = None, model_synth: str = None):
        # Tiered Model Configuration (Ollama-first)
        self.model_bulk = model_bulk or os.getenv("OLLAMA_MODEL_BULK", "ministral-3:8b")
        self.model_synth = model_synth or os.getenv("OLLAMA_MODEL_SYNTHESIS", "qwen3.5:397b")
        
        self.ollama_host = os.getenv("OLLAMA_HOST", "https://ollama.com")
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        
        # Budget Tracking
        self.budget = ContextWindowBudget(
            model_name=f"Ollama {self.model_bulk}/{self.model_synth}"
        )
        
        # Initialize Ollama client
        ollama_headers = {}
        if self.ollama_api_key:
            ollama_headers["Authorization"] = f"Bearer {self.ollama_api_key}"
        self.ollama_client = ollama.Client(host=self.ollama_host, headers=ollama_headers)
        
        # Optional: Keep OpenRouter client ONLY as a tertiary fallback if desired, 
        # but the primary directive is Ollama for both.
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_client = None
        if self.openrouter_api_key:
            from openai import OpenAI
            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
            )
            logger.info("OpenRouter fallback available, but Ollama is primary for both tiers.")

        # Local embedding model
        logger.info("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4

    def chat(self, prompt: str, system: str = "You are a senior FDE specialized in codebase analysis.", tier: str = "bulk") -> str:
        model = self.model_synth if tier == "synthesis" else self.model_bulk
        tokens = self.count_tokens(prompt) + self.count_tokens(system)
        
        # Track budget
        self.budget.total_tokens_used += tokens
        logger.info(f"Ollama Request Tier={tier.upper()} Model={model} | Tokens: ~{tokens} | Cumulative: {self.budget.total_tokens_used}")
        
        try:
            # Primary path: Ollama
            try:
                full_prompt = f"{system}\n\n{prompt}"
                response = self.ollama_client.generate(model=model, prompt=full_prompt, stream=False)
                return response.get("response", "").strip()
            except Exception as e:
                # If synthesis model is missing, try falling back to bulk model (Ollama)
                if tier == "synthesis" and "not found" in str(e).lower():
                    logger.warning(f"Synthesis model '{model}' not found in Ollama. Falling back to bulk model '{self.model_bulk}'.")
                    full_prompt = f"{system}\n\n{prompt}"
                    response = self.ollama_client.generate(model=self.model_bulk, prompt=full_prompt, stream=False)
                    return response.get("response", "").strip()
                
                # Tertiary fallback to OpenRouter ONLY if local failure is complete and key exists
                if self.openai_client:
                    logger.info("Ollama failed. Attempting OpenRouter fallback (budget warning)...")
                    response = self.openai_client.chat.completions.create(
                        model=model, # Might need mapping if model names differ
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.choices[0].message.content.strip()
                raise e
        except Exception as e:
            logger.error(f"LLM error ({tier}): {e}")
            return f"Error: {e}"

    def embed(self, text: str) -> List[float]:
        try:
            # Generate embedding locally
            embedding = self.embed_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            return []

class SemanticistAgent:
    def __init__(self, repo_path: str, db_path: str = ".cartography/semantic_index"):
        self.repo_path = repo_path
        self.llm = IntelligentLLMWrapper()
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="module_purpose")

    def _extract_docstring(self, content: str) -> Optional[str]:
        """Simple regex to extract the first docstring."""
        match = re.search(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', content)
        if match:
            return match.group(1).strip('"\' \n\t')
        return None

    def _strip_code_for_analysis(self, content: str) -> str:
        """
        Strips docstrings and comments to ensure purpose is grounded in logic.
        """
        # Strip long docstrings (''' or """)
        content = re.sub(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', '', content)
        # Strip single line comments
        content = re.sub(r'#.*', '', content)
        content = re.sub(r'--.*', '', content)
        # Compact whitespace
        content = re.sub(r'\n\s*\n', '\n', content)
        return content.strip()

    def generate_purpose_statement(self, node: ModuleNode, original_content: str) -> SemanticAnalysisResult:
        code_only = self._strip_code_for_analysis(original_content)
        docstring = self._extract_docstring(original_content)
        
        # Truncate if too long
        code_fragment = code_only[:8000]
        
        prompt = f"""
Analyze the implementation of the file `{node.path}`. 
Focus ONLY on the CODE logic below to define its purpose.

DOCSTRING (from file):
{docstring if docstring else "No docstring provided."}

CODE (implementation):
{code_fragment}

TASK:
1. Provide a 2-3 sentence 'Purpose Statement' explaining WHAT this module does (business logic) based on the CODE only.
2. Compare the 'Purpose Statement' with the provided 'DOCSTRING'. If the docstring is misleading, outdated, or generic relative to the CODE, flag it as 'Doc Drift'.

FORMAT:
Purpose: [Your 2-3 sentence statement]
Drift: [Yes/No]
DriftReason: [Brief explanation if Yes]
"""
        response = self.llm.chat(prompt)
        logger.debug(f"LLM Raw Response for {node.path}:\n{response}")
        
        # Parse response using more robust regex that ignores markdown and is flexible with whitespace
        # Capture Purpose: ... up until any variation of Drift:
        purpose_match = re.search(r"Purpose:\s*(.*?)(?=\s*[*_]*Drift[:*_]|$)", response, re.IGNORECASE | re.DOTALL)
        drift_match = re.search(r"Drift[:*_ \t]*(Yes|No)", response, re.IGNORECASE)
        reason_match = re.search(r"DriftReason[:*_ \t]*(.*)", response, re.IGNORECASE | re.DOTALL)
        
        purpose = purpose_match.group(1).strip() if purpose_match else "Could not extract purpose."
        # Clean markdown bold/italic
        purpose = re.sub(r'[*_]{1,3}', '', purpose)
        # Final safety: strip anything that looks like a Drift: label if it leaked in
        purpose = re.split(r'(?i)\n?\s*Drift:', purpose)[0].strip()
        
        is_drift = False
        if drift_match:
            is_drift = drift_match.group(1).lower() == "yes"
        
        drift_reason = reason_match.group(1).strip() if reason_match else None
        if drift_reason:
            drift_reason = re.sub(r'[*_]{1,3}', '', drift_reason).strip()
        
        # Generate embedding
        embedding = self.llm.embed(purpose)
        
        # Store in ChromaDB (using upsert to overwrite old broken data)
        self.collection.upsert(
            ids=[node.id],
            embeddings=[embedding] if embedding else None,
            documents=[purpose],
            metadatas=[{"path": node.path, "is_drift": bool(is_drift)}]
        )
        
        # Log to trace
        default_trace.log_action(
            agent="Semanticist",
            action="generate_purpose",
            evidence=f"LLM inference ({self.llm.model_bulk}) + implementation analysis",
            confidence=0.8,
            metadata={"path": node.path, "is_drift": bool(is_drift), "model": self.llm.model_bulk}
        )

        return SemanticAnalysisResult(
            module_id=node.id,
            purpose_statement=purpose,
            is_doc_drift=bool(is_drift),
            doc_drift_explanation=drift_reason,
            embedding=embedding
        )

    def cluster_into_domains(self, n_clusters: int = None):
        """
        Fetches all embeddings from ChromaDB and clusters them.
        If n_clusters is None, it uses the elbow method or a sensible default.
        """
        data = self.collection.get(include=['embeddings', 'metadatas', 'documents'])
        ids = data['ids']
        embeddings = data['embeddings']
        
        if embeddings is None or len(embeddings) < 2:
            logger.warning("Not enough data to cluster.")
            return {}

        X = np.array(embeddings)
        num_samples = len(X)
        
        # Auto-select n_clusters if not provided
        if n_clusters is None:
            if num_samples <= 5:
                n_clusters = 2
            else:
                # Simple rule of thumb: sqrt(n/2)
                n_clusters = int(np.sqrt(num_samples / 2))
                n_clusters = max(2, min(n_clusters, 8)) # Keep between 2 and 8
            logger.info(f"Auto-selected n_clusters={n_clusters} for {num_samples} samples.")

        if num_samples < n_clusters:
            n_clusters = num_samples

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto').fit(X)
        labels = kmeans.labels_
        
        results = {}
        for i, label in enumerate(labels):
            results[ids[i]] = f"Domain_{label}"
            
        # Labeling clusters using LLM
        cluster_summaries = {}
        for label in range(n_clusters):
            idx = [i for i, l in enumerate(labels) if l == label]
            # Include both path and purpose for better context
            modules_info = [f"File: {data['metadatas'][i]['path']}\nPurpose: {data['documents'][i]}" for i in idx[:5]]
            
            prompt = f"Given these module descriptions (file path and purpose), suggest a 1-2 word business domain name. Prefer standard categories like 'ingestion', 'transformation', 'serving', 'monitoring', 'marts', 'staging', 'infrastructure' if they fit.\n\nDESCRIPTIONS:\n" + "\n---\n".join(modules_info)
            domain_name = self.llm.chat(prompt, system="You are an expert software architect. Give only the domain name.")
            # Clean domain name
            domain_name = re.sub(r'[*_]{1,3}', '', domain_name).strip().strip('"')
            cluster_summaries[f"Domain_{label}"] = domain_name

        # Map back to human names
        final_mapping = {mid: cluster_summaries[domain] for mid, domain in results.items()}
        
        # Log to trace
        default_trace.log_action(
            agent="Semanticist",
            action="cluster_domains",
            evidence=f"K-Means + LLM labeling ({self.llm.model_bulk})",
            confidence=0.75,
            metadata={"n_clusters": n_clusters, "mapping": final_mapping}
        )
        
        return final_mapping

