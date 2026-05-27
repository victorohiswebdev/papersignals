"""Random Forest classifier training pipeline for papersignals Phase 2.

Trains a calibrated Random Forest classifier on labeled human vs AI
text using the 7 signal metrics as features.

The trained model produces calibrated probability estimates (0-100)
that replace or augment the heuristic weighted-average composite score.

Pipeline:
  1. Load labeled training data (human papers + synthetic AI text)
  2. Run analyzers on both classes to extract feature vectors
  3. Train RF with cross-validation
  4. Calibrate probabilities (Platt scaling)
  5. Save model + metadata for inference
"""

from __future__ import annotations

import json
import logging
import os
import pickle  # noqa: S403 — we only load our own trusted models
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from joblib import dump, load
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from papersignals.classifier.features import (
    NUM_FEATURES,
    extract_features_from_analysis,
    features_to_dict,
    get_feature_names,
)
from papersignals.corpus.corpus_db import CorpusDB

logger = logging.getLogger(__name__)

# Default model path
MODEL_DIR = os.path.expanduser("~/.papersignals/models")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "rf_classifier.joblib")
DEFAULT_METADATA_PATH = os.path.join(MODEL_DIR, "rf_metadata.json")


@dataclass
class ClassifierMetadata:
    """Metadata for a trained classifier model."""

    version: str = "0.2.0"
    model_type: str = "RandomForest + CalibratedClassifierCV"
    num_features: int = NUM_FEATURES
    feature_names: List[str] = field(default_factory=get_feature_names)
    training_date: str = ""
    num_human_samples: int = 0
    num_ai_samples: int = 0
    cv_folds: int = 5
    cv_accuracy_mean: float = 0.0
    cv_accuracy_std: float = 0.0
    test_accuracy: float = 0.0
    test_f1: float = 0.0
    test_roc_auc: float = 0.0
    calibration_method: str = "sigmoid"
    signal_importances: Dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class RFClassifier:
    """Random Forest classifier for AI text detection.

    Trains on labeled human/AI text using the 7 signal features,
    with calibrated probability output.

    Args:
        model_path: Path to save/load the trained model.
        metadata_path: Path to save/load model metadata.
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        metadata_path: str = DEFAULT_METADATA_PATH,
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.model: Any = None
        self.metadata: Optional[ClassifierMetadata] = None
        os.makedirs(MODEL_DIR, exist_ok=True)

    # ----------------------------------------------------------------
    # Training
    # ----------------------------------------------------------------

    def train(
        self,
        human_features: np.ndarray,
        ai_features: np.ndarray,
        cv_folds: int = 5,
        test_size: float = 0.2,
        calibration: str = "sigmoid",
        random_state: int = 42,
    ) -> ClassifierMetadata:
        """Train a calibrated RF classifier on human vs AI features.

        Args:
            human_features: (n_human, NUM_FEATURES) array from human texts.
            ai_features: (n_ai, NUM_FEATURES) array from AI-generated texts.
            cv_folds: Number of cross-validation folds.
            test_size: Fraction of data to hold out for testing.
            calibration: 'sigmoid' (Platt) or 'isotonic'.
            random_state: Random seed for reproducibility.

        Returns:
            ClassifierMetadata with training results.
        """
        logger.info(
            "Training RF classifier: %d human + %d AI samples, %d features",
            human_features.shape[0],
            ai_features.shape[0],
            human_features.shape[1],
        )

        # Create labels: 1 = human, 0 = AI
        X = np.vstack([human_features, ai_features])
        y = np.hstack([
            np.ones(human_features.shape[0], dtype=int),
            np.zeros(ai_features.shape[0], dtype=int),
        ])

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y,
        )

        # Cross-validation on training set
        logger.info("Running %d-fold cross-validation ...", cv_folds)
        base_rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )

        cv_scores = cross_val_score(
            base_rf, X_train, y_train,
            cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state),
            scoring="accuracy",
        )
        logger.info(
            "CV accuracy: %.4f ± %.4f",
            cv_scores.mean(),
            cv_scores.std(),
        )

        # Train final RF on full training set
        logger.info("Training final RF on full training set ...")
        base_rf.fit(X_train, y_train)

        # Calibrate — use isotonic or sigmoid calibration
        # Train calibrator on a holdout split from training data
        X_cal, X_train_final, y_cal, y_train_final = train_test_split(
            X_train, y_train, test_size=0.7, random_state=random_state, stratify=y_train,
        )

        logger.info("Calibrating probabilities (%s) ...", calibration)
        calibrated = CalibratedClassifierCV(
            base_rf,
            method=calibration,
            cv=3,
        )
        calibrated.fit(X_cal, y_cal)

        self.model = calibrated

        # Evaluate on test set
        y_pred = calibrated.predict(X_test)
        y_prob = calibrated.predict_proba(X_test)[:, 1]  # probability of human

        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_prob)

        logger.info(
            "Test set — accuracy: %.4f, F1: %.4f, ROC-AUC: %.4f",
            accuracy, f1, roc_auc,
        )

        # Feature importances
        importances = base_rf.feature_importances_
        feature_names = get_feature_names()
        signal_importances = {
            name: float(imp * 100)
            for name, imp in sorted(
                zip(feature_names, importances),
                key=lambda x: -x[1],
            )
        }

        # Build metadata
        self.metadata = ClassifierMetadata(
            training_date=time.strftime("%Y-%m-%dT%H:%M:%S"),
            num_human_samples=human_features.shape[0],
            num_ai_samples=ai_features.shape[0],
            cv_folds=cv_folds,
            cv_accuracy_mean=float(cv_scores.mean()),
            cv_accuracy_std=float(cv_scores.std()),
            test_accuracy=float(accuracy),
            test_f1=float(f1),
            test_roc_auc=float(roc_auc),
            calibration_method=calibration,
            signal_importances=signal_importances,
        )

        # Save
        self._save()

        return self.metadata

    def train_from_corpus(
        self,
        corpus_db: Optional[CorpusDB] = None,
        human_papers_limit: int = 500,
        ai_papers_limit: int = 500,
        cv_folds: int = 5,
        test_size: float = 0.2,
    ) -> ClassifierMetadata:
        """Train classifier using corpus DB + synthetic AI generation.

        Args:
            corpus_db: CorpusDB instance. Uses default if None.
            human_papers_limit: Max human papers to use.
            ai_papers_limit: Max AI samples to generate.
            cv_folds: Cross-validation folds.
            test_size: Holdout fraction.

        Returns:
            ClassifierMetadata with training results.
        """
        if corpus_db is None:
            corpus_db = CorpusDB()

        # Load human paper analyses
        analyses = corpus_db.get_all_analyses()
        if not analyses:
            raise ValueError(
                "No analyzed papers in corpus. Run 'papersignals corpus update' first."
            )

        logger.info("Loaded %d analyzed papers from corpus", len(analyses))

        # Cap at limit
        analyses = analyses[:human_papers_limit]

        # Extract human features
        human_features_list: List[np.ndarray] = []
        human_metadata: List[Dict[str, Any]] = []

        for analysis in analyses:
            signals = {
                "burstiness": analysis.burstiness,
                "transition_density": analysis.transition_density,
                "lexical_diversity": analysis.lexical_diversity,
                "vocabulary_fingerprint": analysis.vocabulary_fingerprint,
                "paragraph_uniformity": analysis.paragraph_uniformity,
                "readability": analysis.readability,
                "perplexity": analysis.perplexity,
            }
            try:
                features = extract_features_from_analysis(signals)
                human_features_list.append(features)
                human_metadata.append({"paper_id": analysis.paper_id, "label": "human"})
            except Exception as e:
                logger.warning("Failed to extract features from %s: %s", analysis.paper_id, e)

        human_features = np.array(human_features_list)
        logger.info("Extracted features from %d human papers", human_features.shape[0])

        # Generate synthetic AI features
        from papersignals.classifier.synthetic_ai import SyntheticAIGenerator
        from papersignals.cli import run_analysis
        import tempfile

        generator = SyntheticAIGenerator(seed=42)
        ai_features_list: List[np.ndarray] = []

        # Get the corresponding human papers for AI generation
        papers = corpus_db.get_all_papers()
        paper_by_id = {p.get("arxiv_id", ""): p for p in papers}

        count = 0
        for analysis in analyses:
            if count >= ai_papers_limit:
                break

            paper = paper_by_id.get(analysis.paper_id)
            if not paper or not paper.get("abstract"):
                continue

            abstract = paper["abstract"]
            if len(abstract.strip()) < 50:
                continue

            # Generate AI version
            ai_text = generator.generate(abstract)

            # Run analyzers on AI text
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False, encoding="utf-8"
                ) as f:
                    f.write(ai_text)
                    tmp_path = f.name

                try:
                    ai_analysis = run_analysis(tmp_path)
                finally:
                    os.unlink(tmp_path)

                ai_signals = ai_analysis.get("signals", {})
                ai_features = extract_features_from_analysis(ai_signals)
                ai_features_list.append(ai_features)
                count += 1

                if count % 100 == 0:
                    logger.info("  Generated %d AI samples ...", count)

            except Exception as e:
                logger.debug("AI generation failed for %s: %s", analysis.paper_id, e)
                continue

        if not ai_features_list:
            raise ValueError("Failed to generate any AI samples.")

        ai_features = np.array(ai_features_list)
        logger.info("Generated %d AI text samples", ai_features.shape[0])

        # Train
        return self.train(
            human_features,
            ai_features,
            cv_folds=cv_folds,
            test_size=test_size,
        )

    # ----------------------------------------------------------------
    # Inference
    # ----------------------------------------------------------------

    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class and probability for feature vectors.

        Args:
            features: (n_samples, NUM_FEATURES) array.

        Returns:
            Tuple of (predictions, probabilities).
            predictions: 1 = human, 0 = AI.
            probabilities: probability of being human (0-1).
        """
        if self.model is None:
            self._load()

        preds = self.model.predict(features)
        probs = self.model.predict_proba(features)[:, 1]
        return preds, probs

    def predict_from_signals(
        self, signals: Dict[str, Any]
    ) -> Tuple[int, float]:
        """Predict from analyzer signal dicts (single sample).

        Args:
            signals: Dict from cli.run_analysis()['signals'].

        Returns:
            Tuple of (prediction, probability).
            prediction: 1 = human, 0 = AI.
            probability: 0-1 score (higher = more human-like).
        """
        features = extract_features_from_analysis(signals).reshape(1, -1)
        pred, prob = self.predict(features)
        return int(pred[0]), float(prob[0])

    # ----------------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------------

    def _save(self) -> None:
        """Save model and metadata to disk."""
        if self.model is None:
            raise ValueError("No model to save.")

        # Save model
        dump(self.model, self.model_path)
        logger.info("Model saved to %s", self.model_path)

        # Save metadata
        if self.metadata:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info("Metadata saved to %s", self.metadata_path)

    def _load(self) -> None:
        """Load model and metadata from disk."""
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"No trained model found at {self.model_path}. "
                "Run train_from_corpus() first."
            )

        self.model = load(self.model_path)

        if os.path.isfile(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.metadata = ClassifierMetadata(**data)

        logger.info("Model loaded from %s", self.model_path)

    def is_trained(self) -> bool:
        """Check if a trained model exists on disk."""
        return os.path.isfile(self.model_path)

    def summary(self) -> str:
        """Print a formatted summary of the trained model."""
        if self.model is None:
            try:
                self._load()
            except FileNotFoundError:
                return "No trained model available."

        if not self.metadata:
            return "Model loaded but metadata not available."

        m = self.metadata
        lines = [
            f"📊 RF Classifier Summary",
            f"   Model: {m.model_type} v{m.version}",
            f"   Training data: {m.num_human_samples} human + {m.num_ai_samples} AI",
            f"   Features: {m.num_features}",
            f"   Calibration: {m.calibration_method}",
            f"",
            f"   Cross-val accuracy: {m.cv_accuracy_mean:.4f} ± {m.cv_accuracy_std:.4f}",
            f"   Test accuracy: {m.test_accuracy:.4f}",
            f"   Test F1: {m.test_f1:.4f}",
            f"   Test ROC-AUC: {m.test_roc_auc:.4f}",
            f"",
            f"   Top features by importance:",
        ]

        for name, imp in list(m.signal_importances.items())[:8]:
            lines.append(f"     {name}: {imp:.2f}%")

        lines.append(f"")
        lines.append(f"   Trained: {m.training_date}")

        return "\n".join(lines)
