from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from pathlib import Path
import json
from typing import Dict, Any, Tuple, Optional
import time
from functools import lru_cache

class ContentAnalyzer:
    def __init__(self, model_name="paraphrase-MiniLM-L3-v2"):
        """Initialize with a very lightweight model (~50MB)"""
        try:
            self.model = SentenceTransformer(model_name)
            # Reduce model memory usage
            self.model.max_seq_length = 128
            print("Initialized lightweight content analyzer...")
        except Exception as e:
            logging.error(f"Model initialization failed: {str(e)}")
            self.model = None

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for analysis."""
        text = ' '.join(text.split())
        return text[:512]  # Limit text length for memory

    @lru_cache(maxsize=1000)
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get text embedding with caching"""
        return self.model.encode(text, convert_to_tensor=True).cpu().numpy()

    def _compute_similarity(self, text_emb: np.ndarray, category: str) -> float:
        """Compute cosine similarity between text and category"""
        category_emb = self._get_embedding(category)
        return float(np.dot(text_emb, category_emb) / 
                    (np.linalg.norm(text_emb) * np.linalg.norm(category_emb)))

    def _extract_main_content(self, content: Any) -> str:
        """Extract main content from different data types."""
        try:
            if isinstance(content, dict):
                # Try to get content from different possible dictionary keys
                for key in ['text', 'text_content', 'content', 'body', 'url', 'title']:
                    if key in content and content[key]:
                        return str(content[key])
                return str(content)
            elif isinstance(content, str):
                return content
            else:
                return str(content)
        except Exception as e:
            logging.error(f"Content extraction failed: {str(e)}")
            return ""

    def is_relevant_content(self, text: str, categories: list) -> Tuple[bool, Optional[str], float]:
        if not self.model:
            return False, None, 0.0, ""
        
        try:
            text = self._clean_text(text)
            text_emb = self._get_embedding(text)
            
            # Find best matching category
            similarities = [(cat, self._compute_similarity(text_emb, cat)) 
                          for cat in categories]
            best_category, confidence = max(similarities, key=lambda x: x[1])
            
            is_relevant = confidence > 0.3  # Lower threshold for lightweight model
            
            return (
                is_relevant,
                best_category if is_relevant else None,
                confidence,
                text[:200] + "..." if len(text) > 200 else text  # Simple summary
            )
            
        except Exception as e:
            logging.error(f"Classification failed: {str(e)}")
            return False, None, 0.0, ""

    def filter_content(self, content_dict: Dict[str, Any], categories: list) -> Dict[str, Any]:
        filtered_content = {}
        
        try:
            for key, content in content_dict.items():
                main_text = self._extract_main_content(content)
                if not main_text:  # Skip empty content
                    continue
                    
                is_relevant, category, confidence, summary = self.is_relevant_content(main_text, categories)
                
                if is_relevant and confidence > 0.3:  # Lowered threshold for better recall
                    filtered_content[key] = {
                        'text': main_text,
                        'category': category,
                        'confidence': confidence,
                        'summary': summary
                    }
        except Exception as e:
            logging.error(f"Content filtering failed: {str(e)}")
            
        return filtered_content