import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)

class FSSAIRAGService:
    def __init__(self):
        self.regulations_dir = settings.REGULATIONS_DIR
        self.chroma_dir = settings.CHROMA_DB_DIR
        self.collection_name = "fssai_regulations"
        self.documents: List[Dict[str, Any]] = []
        self.chroma_collection = None
        self._load_corpus()
        self._init_vector_store()

    def _load_corpus(self):
        """Loads all statutory FSSAI JSON regulation documents from disk"""
        self.documents = []
        json_files = list(self.regulations_dir.glob("*.json"))
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    docs = json.load(f)
                    self.documents.extend(docs)
            except Exception as e:
                logger.error(f"Failed to load regulation file {jf}: {e}")
        logger.info(f"Loaded {len(self.documents)} statutory FSSAI regulation clauses into memory.")

    def _init_vector_store(self):
        """Initializes ChromaDB collection with persistent storage"""
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            # Initialize Persistent Chroma Client
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            
            # Use Chroma's high-speed ONNX DefaultEmbeddingFunction (all-MiniLM-L6-v2)
            emb_fn = embedding_functions.DefaultEmbeddingFunction()
            
            self.chroma_collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=emb_fn,
                metadata={"description": "FSSAI Food Safety and Standards Regulations"}
            )
            
            # Check if collection needs update, then upsert
            existing_count = self.chroma_collection.count()
            if (existing_count != len(self.documents)) and self.documents:
                logger.info(f"Indexing ChromaDB collection with {len(self.documents)} statutory clauses...")
                ids = [doc["id"] for doc in self.documents]
                documents = [f"{doc['title']}\n{doc['section']}\n{doc['text']}" for doc in self.documents]
                metadatas = [
                    {
                        "regulation": doc["regulation"],
                        "section": doc["section"],
                        "category": doc["category"],
                        "title": doc["title"]
                    }
                    for doc in self.documents
                ]
                self.chroma_collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info("ChromaDB indexing completed.")
        except Exception as e:
            logger.warning(f"ChromaDB / SentenceTransformer init deferred: {e}. Semantic keyword fallback active.")
            self.chroma_collection = None

    def retrieve_relevant_clauses(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant statutory clauses for a given query or packaging doubt.
        Supports both ChromaDB vector search and an embedded BM25/keyword matcher.
        """
        if self.chroma_collection is not None:
            try:
                results = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=min(top_k, len(self.documents))
                )
                clauses = []
                if results and "ids" in results and results["ids"]:
                    retrieved_ids = results["ids"][0]
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0]*len(retrieved_ids)
                    
                    id_to_doc = {d["id"]: d for d in self.documents}
                    for doc_id, dist in zip(retrieved_ids, distances):
                        if doc_id in id_to_doc:
                            item = dict(id_to_doc[doc_id])
                            item["similarity_score"] = round(1.0 - (dist / 2.0) if dist is not None else 0.85, 3)
                            clauses.append(item)
                    return clauses
            except Exception as e:
                logger.error(f"ChromaDB query failed: {e}. Falling back to keyword search.")

        # Fallback keyword and semantic similarity matcher
        scored_docs = []
        q_tokens = set(query.lower().split())
        for doc in self.documents:
            doc_str = (doc["title"] + " " + doc["text"] + " " + " ".join(doc.get("keywords", []))).lower()
            # Token overlap score
            overlap = sum(1 for t in q_tokens if t in doc_str)
            score = overlap / (len(q_tokens) + 1)
            scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_results = []
        for score, doc in scored_docs[:top_k]:
            item = dict(doc)
            item["similarity_score"] = round(float(score), 3)
            top_results.append(item)
        return top_results

rag_service = FSSAIRAGService()
