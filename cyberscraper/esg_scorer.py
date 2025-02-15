import numpy as np
from typing import Dict, Any, List, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer

class ESGScorer:
    def __init__(self):
        self.weights = {
            'environmental': 0.35,
            'social': 0.35,
            'governance': 0.30
        }
        
        self.keywords = {
            'environmental': [
                'sustainability', 'renewable', 'carbon', 'emissions', 'climate',
                'environmental', 'green', 'energy', 'waste', 'recycling'
            ],
            'social': [
                'community', 'diversity', 'inclusion', 'employee', 'health',
                'safety', 'human rights', 'labor', 'fair', 'social'
            ],
            'governance': [
                'transparency', 'compliance', 'board', 'audit', 'risk',
                'ethics', 'corruption', 'governance', 'regulatory', 'policy'
            ],
            'blockchain': [
                'blockchain', 'crypto', 'token', 'web3', 'decentralized',
                'smart contract', 'consensus', 'distributed ledger'
            ]
        }
        
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000
        )

    def _calculate_category_score(self, text: str, category: str) -> float:
        """Calculate score for a specific category based on keyword presence."""
        if not text:
            return 0.0
            
        keywords = self.keywords[category]
        text_lower = text.lower()
        
        # Calculate keyword frequency
        keyword_count = sum(text_lower.count(k.lower()) for k in keywords)
        # Normalize by text length
        score = keyword_count / (len(text.split()) + 1)  # Add 1 to avoid division by zero
        
        return min(score * 100, 100)  # Cap at 100

    def _calculate_sentiment_impact(self, text: str) -> float:
        """Calculate sentiment impact on scores."""
        try:
            from textblob import TextBlob
            sentiment = TextBlob(text).sentiment.polarity
            # Convert [-1, 1] to [0.5, 1.5] range for score multiplication
            return 1 + (sentiment * 0.5)
        except:
            return 1.0  # Neutral impact if TextBlob fails

    def calculate_scores(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive ESG and blockchain scores."""
        try:
            results = {
                'scores': {},
                'category_details': {},
                'overall_score': 0.0,
                'blockchain_alignment': 0.0
            }
            
            # Calculate individual category scores
            for category in self.weights.keys():
                if category in cleaned_data:
                    category_text = ' '.join(cleaned_data[category])
                    base_score = self._calculate_category_score(category_text, category)
                    sentiment_impact = self._calculate_sentiment_impact(category_text)
                    
                    final_score = base_score * sentiment_impact
                    results['scores'][category] = round(final_score, 2)
                    
                    results['category_details'][category] = {
                        'base_score': round(base_score, 2),
                        'sentiment_impact': round(sentiment_impact, 2),
                        'final_score': round(final_score, 2)
                    }
            
            # Calculate overall ESG score
            weighted_scores = [
                results['scores'].get(cat, 0) * weight 
                for cat, weight in self.weights.items()
            ]
            results['overall_score'] = round(sum(weighted_scores), 2)
            
            # Calculate blockchain/crypto alignment
            if 'clean_text' in cleaned_data:
                blockchain_score = self._calculate_category_score(
                    cleaned_data['clean_text'], 
                    'blockchain'
                )
                results['blockchain_alignment'] = round(blockchain_score, 2)
            
            return results
            
        except Exception as e:
            logging.error(f"Scoring failed: {str(e)}")
            return {
                'scores': {},
                'category_details': {},
                'overall_score': 0.0,
                'blockchain_alignment': 0.0,
                'error': str(e)
            }
