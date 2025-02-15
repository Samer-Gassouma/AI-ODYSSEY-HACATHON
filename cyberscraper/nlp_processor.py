import spacy
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    pipeline
)
from typing import Dict, List, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import json
import requests
import ipfshttpclient
from web3.auto import w3

class NLPProcessor:
    def __init__(self):
        # Load models
        self.nlp = spacy.load("en_core_web_sm")
        self.finbert = pipeline("sentiment-analysis", 
                              model="ProsusAI/finbert")
        self.esg_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-esg")
        self.esg_model = AutoModelForSequenceClassification.from_pretrained(
            "yiyanghkust/finbert-esg"
        )
        
    def _process_ipfs_content(self, ipfs_hash: str) -> str:
        """Fetch and process content from IPFS"""
        try:
            client = ipfshttpclient.connect()
            content = client.cat(ipfs_hash)
            return content.decode('utf-8')
        except Exception as e:
            logging.error(f"IPFS fetch error: {e}")
            return ""

    def _process_arweave_content(self, ar_id: str) -> str:
        """Fetch and process content from Arweave"""
        try:
            response = requests.get(f"https://arweave.net/{ar_id}")
            return response.text
        except Exception as e:
            logging.error(f"Arweave fetch error: {e}")
            return ""

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Comprehensive NLP analysis of text"""
        doc = self.nlp(text)
        
        # Extract named entities
        entities = {
            ent.label_: ent.text 
            for ent in doc.ents 
            if ent.label_ in ['ORG', 'DATE', 'MONEY', 'PERCENT']
        }
        
        # Get key phrases using noun chunks
        key_phrases = [
            chunk.text 
            for chunk in doc.noun_chunks 
            if len(chunk.text.split()) > 1
        ]
        
        # Financial sentiment analysis
        financial_sentiment = self.finbert(text[:512])[0]
        
        # ESG classification
        esg_inputs = self.esg_tokenizer(text[:512], return_tensors="pt")
        esg_outputs = self.esg_model(**esg_inputs)
        esg_scores = torch.nn.functional.softmax(esg_outputs.logits, dim=1)
        
        esg_categories = ['Environmental', 'Social', 'Governance']
        esg_classification = {
            cat: float(score)
            for cat, score in zip(esg_categories, esg_scores[0])
        }
        
        return {
            'entities': entities,
            'key_phrases': key_phrases,
            'sentiment': {
                'label': financial_sentiment['label'],
                'score': float(financial_sentiment['score'])
            },
            'esg_classification': esg_classification,
            'summary': ' '.join(sent.text for sent in doc.sents)[:200]
        }

    def process_decentralized_storage(self, url: str) -> Dict[str, Any]:
        """Process content from decentralized storage"""
        if 'ipfs://' in url:
            ipfs_hash = url.replace('ipfs://', '')
            content = self._process_ipfs_content(ipfs_hash)
        elif 'ar://' in url:
            ar_id = url.replace('ar://', '')
            content = self._process_arweave_content(ar_id)
        else:
            return None
            
        if content:
            return self.analyze_text(content)
        return None
