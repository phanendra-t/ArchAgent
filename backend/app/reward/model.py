"""Reward Model — MLPClassifier wrapper for scoring findings."""
from __future__ import annotations
import os
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from app.config import get_settings


class RewardModel:
    """Wrapper around sklearn MLPClassifier for finding validity prediction."""
    
    def __init__(self):
        self.model: MLPClassifier | None = None
        self.scaler: StandardScaler | None = None
        self._loaded = False
    
    def is_available(self) -> bool:
        """Check if a trained model exists."""
        if self._loaded and self.model is not None:
            return True
        return self._try_load()
    
    def _try_load(self) -> bool:
        """Try to load a saved model from disk."""
        settings = get_settings()
        model_path = Path(settings.reward_model_path)
        scaler_path = model_path.with_suffix(".scaler.joblib")
        
        if model_path.exists() and scaler_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self._loaded = True
                return True
            except Exception:
                return False
        return False
    
    def predict(self, features: np.ndarray) -> float:
        """Predict probability that a finding is valid (0.0 to 1.0)."""
        if self.model is None or self.scaler is None:
            return 1.0  # Default: assume valid if no model
        
        # Reshape for single sample if needed
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Get probability of being "valid" (class 1)
        probas = self.model.predict_proba(features_scaled)
        return float(probas[0][1])  # Probability of positive class
    
    def predict_batch(self, features: np.ndarray) -> list[float]:
        """Predict probabilities for multiple findings."""
        if self.model is None or self.scaler is None:
            return [1.0] * len(features)
        
        features_scaled = self.scaler.transform(features)
        probas = self.model.predict_proba(features_scaled)
        return [float(p[1]) for p in probas]
    
    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train or retrain the model on annotated data."""
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train MLP
        self.model = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.15,
            random_state=42,
            alpha=0.001,  # L2 regularization
        )
        self.model.fit(X_scaled, y)
        
        # Evaluate
        predictions = self.model.predict(X_scaled)
        
        # Cross-validation if enough data
        if len(X) >= 10:
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=min(5, len(X) // 2))
            accuracy = float(cv_scores.mean())
        else:
            accuracy = float((predictions == y).mean())
        
        metrics = {
            "accuracy": accuracy,
            "precision": float(precision_score(y, predictions, zero_division=0)),
            "recall": float(recall_score(y, predictions, zero_division=0)),
            "f1": float(f1_score(y, predictions, zero_division=0)),
        }
        
        # Save model
        self._save()
        self._loaded = True
        
        return metrics
    
    def _save(self):
        """Persist model to disk."""
        settings = get_settings()
        model_path = Path(settings.reward_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, model_path.with_suffix(".scaler.joblib"))


# Singleton instance
_reward_model: RewardModel | None = None


def get_reward_model() -> RewardModel:
    """Get the singleton reward model instance."""
    global _reward_model
    if _reward_model is None:
        _reward_model = RewardModel()
    return _reward_model
