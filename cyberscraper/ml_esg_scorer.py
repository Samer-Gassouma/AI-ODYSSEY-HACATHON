import json
import requests
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
import shap
import logging
from typing import Dict, Any
from web3 import Web3
from datetime import datetime, timedelta
import os

class MLESGScorer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{os.getenv("INFURA_API_KEY")}'))
        self.scaler = MinMaxScaler(feature_range=(0, 100))
        # Define ESG-related features
        self.feature_names = [
            'energy_efficiency',
            'carbon_offset_ratio',
            'renewable_energy_usage',
            'waste_management_score',
            'social_impact_score',
            'employee_welfare_index',
            'community_engagement_rate',
            'governance_score',
            'dao_participation',
            'transparency_score'
        ]
        self.model = self._initialize_model()
        self.explainer = None
        self.lime_explainer = None
        
        # Try to import LIME
        try:
            from lime import lime_tabular
            self.has_lime = True
        except ImportError:
            logging.warning("LIME not available, will skip LIME explanations")
            self.has_lime = False

    def _initialize_model(self):
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1
        )
        
        # Generate synthetic training data with realistic ESG patterns
        np.random.seed(42)
        X_train = np.random.rand(1000, len(self.feature_names))
        
        # Add realistic correlations
        X_train[:, 0] = X_train[:, 4] * 0.8 + X_train[:, 0] * 0.2  # L2 adoption affects energy efficiency
        X_train[:, 1] = X_train[:, 2] * 0.6 + X_train[:, 1] * 0.4  # Governance affects carbon offsets
        
        # Generate target values with weighted importance - ensure weights match feature count
        weights = [0.15, 0.15, 0.12, 0.12, 0.10, 0.10, 0.08, 0.08, 0.05, 0.05]  # Sum = 1.0
        y_train = np.dot(X_train, weights) * 100
        
        model.fit(X_train, y_train)
        self.explainer = shap.TreeExplainer(model)
        
        # Initialize LIME only if available
        if self.has_lime:
            try:
                from lime import lime_tabular
                self.lime_explainer = lime_tabular.LimeTabularExplainer(
                    X_train,
                    feature_names=self.feature_names,
                    mode='regression'
                )
            except Exception as e:
                logging.error(f"LIME initialization failed: {e}")
                self.has_lime = False
                
        return model

    def _get_energy_metrics(self) -> Dict[str, float]:
        try:
            # Get L1 vs L2 transaction data
            l1_gas = self.w3.eth.get_block('latest').gasUsed
            optimism_endpoint = f"https://optimism-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
            w3_l2 = Web3(Web3.HTTPProvider(optimism_endpoint))
            l2_gas = w3_l2.eth.get_block('latest').gasUsed
            
            # Calculate efficiency metrics
            l2_efficiency = 1 - (l2_gas / l1_gas)
            energy_per_gas = 0.000000392  # kWh per gas unit (estimate)
            
            return {
                "l1_energy_kWh": l1_gas * energy_per_gas,
                "l2_energy_kWh": l2_gas * energy_per_gas,
                "l2_efficiency": l2_efficiency
            }
        except Exception as e:
            logging.error(f"Energy metrics error: {e}")
            return {"l1_energy_kWh": 0, "l2_energy_kWh": 0, "l2_efficiency": 0}

    def _get_klima_metrics(self) -> Dict[str, float]:
        try:
            # Query KlimaDAO subgraph
            query = """
            {
              klimaStakings(first: 1) {
                totalSupply
                rebaseRate
                carbonLocked
              }
            }
            """
            response = requests.post(
                'https://api.thegraph.com/subgraphs/name/klimadao/klimadao',
                json={'query': query}
            )
            data = response.json()['data']['klimaStakings'][0]
            
            return {
                "carbon_locked": float(data['carbonLocked']),
                "offset_rate": float(data['rebaseRate'])
            }
        except Exception as e:
            logging.error(f"KlimaDAO metrics error: {e}")
            return {"carbon_locked": 0, "offset_rate": 0}

    def _get_dao_metrics(self) -> Dict[str, float]:
        try:
            # Query Snapshot for governance data
            query = """
            {
              proposals(first: 100, orderBy: "created", orderDirection: desc) {
                votes
                quorum
                executed
              }
            }
            """
            response = requests.post(
                'https://hub.snapshot.org/graphql',
                json={'query': query}
            )
            proposals = response.json()['data']['proposals']
            
            # Calculate governance metrics
            total_proposals = len(proposals)
            executed_ratio = sum(1 for p in proposals if p['executed']) / total_proposals
            avg_participation = np.mean([p['votes'] / p['quorum'] for p in proposals])
            
            return {
                "proposal_count": total_proposals,
                "execution_rate": executed_ratio,
                "participation_rate": avg_participation
            }
        except Exception as e:
            logging.error(f"DAO metrics error: {e}")
            return {"proposal_count": 0, "execution_rate": 0, "participation_rate": 0}

    def _extract_features(self, cleaned_data: Dict[str, Any]) -> Dict[str, float]:
        energy = self._get_energy_metrics()
        klima = self._get_klima_metrics()
        dao = self._get_dao_metrics()
        
        features = {
            "energy_efficiency": energy["l2_efficiency"] * 100,
            "carbon_offset_ratio": klima["carbon_locked"] / (energy["l1_energy_kWh"] + 1),
            "renewable_energy_usage": energy["l2_energy_kWh"] / (energy["l1_energy_kWh"] + energy["l2_energy_kWh"]) * 100,
            "waste_management_score": (1 - (energy["l2_energy_kWh"] / (energy["l1_energy_kWh"] + 1))) * 100,
            "social_impact_score": self._calculate_social_score(cleaned_data),
            "employee_welfare_index": float(cleaned_data.get("social", {}).get("employee_welfare", 75.0)),
            "community_engagement_rate": dao["participation_rate"] * 100,
            "governance_score": dao["execution_rate"] * dao["participation_rate"] * 100,
            "dao_participation": dao["participation_rate"] * 100,
            "transparency_score": self._calculate_transparency_score(cleaned_data)
        }
        
        return {k: float(v) for k, v in features.items()}

    def _calculate_social_score(self, cleaned_data: Dict[str, Any]) -> float:
        social_data = cleaned_data.get("social", {})
        score = sum([
            len(social_data.get("community_initiatives", [])) * 10,
            len(social_data.get("social_impact", [])) * 15,
            len(social_data.get("diversity_inclusion", [])) * 15
        ])
        return min(100.0, float(score))

    def _calculate_transparency_score(self, cleaned_data: Dict[str, Any]) -> float:
        # Score based on ESG disclosure frequency and completeness
        env_score = len(cleaned_data.get("environmental", [])) * 2
        social_score = len(cleaned_data.get("social", [])) * 2
        gov_score = len(cleaned_data.get("governance", [])) * 2
        
        return min(100, (env_score + social_score + gov_score) / 3)

    def _get_sustainability_commits(self) -> float:
        # Placeholder for actual GitHub API integration
        return 75.0

    def calculate_esg_score(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            features = self._extract_features(cleaned_data)
            df_features = pd.DataFrame([features])
            
            # Scale features
            df_scaled = pd.DataFrame(
                self.scaler.fit_transform(df_features), 
                columns=self.feature_names
            )
            
            # Generate predictions and SHAP explanations
            predicted_score = float(self.model.predict(df_scaled)[0])
            shap_values = self.explainer(df_scaled)
            
            result = {
                "esg_score": round(predicted_score, 2),
                "features": features,
                "feature_importance": {
                    name: float(importance)
                    for name, importance in zip(self.feature_names, shap_values.values[0])
                },
                "category_scores": {
                    "environmental": round((features["energy_efficiency"] + features["carbon_offset_ratio"]) / 2, 2),
                    "social": round(features["transparency_score"], 2),
                    "governance": round((features["governance_score"] + features["dao_participation"]) / 2, 2)
                }
            }
            
            # Add LIME explanation only if available
            if self.has_lime and self.lime_explainer:
                try:
                    lime_exp = self.lime_explainer.explain_instance(
                        df_scaled.iloc[0], 
                        self.model.predict
                    )
                    result["lime_explanation"] = {
                        feat: float(imp)
                        for feat, imp in lime_exp.as_list()
                    }
                except Exception as e:
                    logging.error(f"LIME explanation failed: {e}")
            
            return result
            
        except Exception as e:
            logging.error(f"ESG scoring failed: {e}")
            return {"error": str(e), "esg_score": 0}
