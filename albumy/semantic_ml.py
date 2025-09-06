# Option B: Semantic Search Implementation
import numpy as np
import json
import os

class SemanticSearchEngine:
    def __init__(self):
        self.embeddings = {}
        
    def generate_image_embedding(self, image_path):
        # Simplified - returns random embedding for demo
        return np.random.randn(512).tolist()
    
    def generate_text_embedding(self, text):
        # Simplified - returns random embedding for demo
        return np.random.randn(512).tolist()
    
    def find_similar(self, query_embedding, top_k=10):
        results = []
        query = np.array(query_embedding)
        for photo_id, emb in self.embeddings.items():
            similarity = np.dot(query, emb) / (np.linalg.norm(query) * np.linalg.norm(emb) + 1e-8)
            results.append((int(photo_id), float(similarity)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

semantic_engine = SemanticSearchEngine()

def integrate_with_upload(photo_id, image_path):
    embedding = semantic_engine.generate_image_embedding(image_path)
    semantic_engine.embeddings[str(photo_id)] = embedding
    return embedding

def semantic_search(query, limit=20):
    query_embedding = semantic_engine.generate_text_embedding(query)
    results = semantic_engine.find_similar(query_embedding, top_k=limit)
    return [photo_id for photo_id, score in results]
