import torch
from torch import nn
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, classification_report
import numpy as np
from typing import List, Dict, Tuple, Optional
import pandas as pd
from loguru import logger
from tqdm import tqdm
import json


class RelevancePredictor:
    """Predict relevance of entities to documents and sections"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load pre-trained model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        
        # Multi-label classifier
        self.mlb = MultiLabelBinarizer()
        self.classifier = None
        
        # Threshold for relevance
        self.threshold = 0.5
        
        # Cache for embeddings
        self.embedding_cache = {}
        
    def encode_text(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts to embeddings"""
        embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Encoding texts"):
            batch = texts[i:i + batch_size]
            
            # Check cache
            batch_embeddings = []
            uncached_indices = []
            uncached_texts = []
            
            for idx, text in enumerate(batch):
                if text in self.embedding_cache:
                    batch_embeddings.append(self.embedding_cache[text])
                else:
                    uncached_indices.append(idx)
                    uncached_texts.append(text)
            
            # Encode uncached texts
            if uncached_texts:
                inputs = self.tokenizer(
                    uncached_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # Mean pooling
                    attention_mask = inputs['attention_mask']
                    embeddings_batch = self._mean_pooling(outputs.last_hidden_state, attention_mask)
                    embeddings_batch = embeddings_batch.cpu().numpy()
                
                # Update cache and results
                for idx, (orig_idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                    embedding = embeddings_batch[idx]
                    self.embedding_cache[text] = embedding
                    batch_embeddings.insert(orig_idx, embedding)
            
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def _mean_pooling(self, model_output: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Mean pooling for sentence embeddings"""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(model_output.size()).float()
        sum_embeddings = torch.sum(model_output * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    def prepare_training_data(
        self,
        documents: List[Dict],
        entity_labels: Dict[str, List[str]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from documents and labels"""
        
        texts = []
        labels = []
        
        for doc in documents:
            doc_id = doc.get("document_id")
            
            # Document level
            if "title" in doc:
                texts.append(doc["title"])
                labels.append(entity_labels.get(doc_id, []))
            
            # Section level
            if "source_text" in doc:
                for section in doc["source_text"]:
                    section_text = section.get("text", "")
                    if section_text:
                        texts.append(section_text[:1000])  # Limit length
                        section_id = f"{doc_id}:{section.get('section_id', 'unknown')}"
                        labels.append(entity_labels.get(section_id, entity_labels.get(doc_id, [])))
        
        # Encode texts
        X = self.encode_text(texts)
        
        # Encode labels
        y = self.mlb.fit_transform(labels)
        
        return X, y
    
    def train_classifier(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2
    ):
        """Train relevance classifier"""
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Training on {X_train.shape[0]} samples, testing on {X_test.shape[0]} samples")
        logger.info(f"Number of unique entities: {y.shape[1]}")
        
        # Build neural network classifier
        input_dim = X_train.shape[1]
        output_dim = y_train.shape[1]
        
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, output_dim),
            nn.Sigmoid()
        ).to(self.device)
        
        # Training
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.classifier.parameters(), lr=0.001)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).to(self.device)
        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        y_test_tensor = torch.FloatTensor(y_test).to(self.device)
        
        # Training loop
        epochs = 50
        batch_size = 32
        
        for epoch in range(epochs):
            self.classifier.train()
            epoch_loss = 0
            
            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i + batch_size]
                batch_y = y_train_tensor[i:i + batch_size]
                
                optimizer.zero_grad()
                outputs = self.classifier(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            # Validation
            if (epoch + 1) % 10 == 0:
                self.classifier.eval()
                with torch.no_grad():
                    val_outputs = self.classifier(X_test_tensor)
                    val_loss = criterion(val_outputs, y_test_tensor)
                    
                    # Calculate metrics
                    y_pred = (val_outputs.cpu().numpy() > self.threshold).astype(int)
                    precision, recall, f1, _ = precision_recall_fscore_support(
                        y_test, y_pred, average='macro', zero_division=0
                    )
                    
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} - "
                        f"Train Loss: {epoch_loss / (len(X_train) / batch_size):.4f}, "
                        f"Val Loss: {val_loss:.4f}, "
                        f"Precision: {precision:.4f}, "
                        f"Recall: {recall:.4f}, "
                        f"F1: {f1:.4f}"
                    )
        
        # Final evaluation
        self.classifier.eval()
        with torch.no_grad():
            final_outputs = self.classifier(X_test_tensor)
            y_pred = (final_outputs.cpu().numpy() > self.threshold).astype(int)
            
            # Detailed classification report
            entity_names = self.mlb.classes_
            report = classification_report(y_test, y_pred, target_names=entity_names[:50])  # Limit display
            logger.info(f"Classification Report:\n{report}")
    
    def predict_relevance(
        self,
        documents: List[Dict],
        entities: List[str]
    ) -> Dict[str, Dict]:
        """Predict entity relevance for documents"""
        
        if self.classifier is None:
            logger.warning("Classifier not trained, using rule-based approach")
            return self._rule_based_prediction(documents, entities)
        
        predictions = {}
        
        for doc in tqdm(documents, desc="Predicting relevance"):
            doc_id = doc.get("document_id")
            predictions[doc_id] = {
                "document_level": {},
                "section_level": {}
            }
            
            # Document level prediction
            if "title" in doc:
                title_embedding = self.encode_text([doc["title"]])[0]
                with torch.no_grad():
                    probs = self.classifier(
                        torch.FloatTensor(title_embedding).unsqueeze(0).to(self.device)
                    ).cpu().numpy()[0]
                
                # Map probabilities to entities
                for idx, entity in enumerate(self.mlb.classes_):
                    if entity in entities and probs[idx] > self.threshold:
                        predictions[doc_id]["document_level"][entity] = float(probs[idx])
            
            # Section level prediction
            if "source_text" in doc:
                for section in doc["source_text"]:
                    section_id = section.get("section_id", "unknown")
                    section_text = section.get("text", "")
                    
                    if section_text:
                        section_embedding = self.encode_text([section_text[:1000]])[0]
                        with torch.no_grad():
                            probs = self.classifier(
                                torch.FloatTensor(section_embedding).unsqueeze(0).to(self.device)
                            ).cpu().numpy()[0]
                        
                        section_predictions = {}
                        for idx, entity in enumerate(self.mlb.classes_):
                            if entity in entities and probs[idx] > self.threshold:
                                section_predictions[entity] = float(probs[idx])
                        
                        if section_predictions:
                            predictions[doc_id]["section_level"][section_id] = section_predictions
        
        return predictions
    
    def _rule_based_prediction(
        self,
        documents: List[Dict],
        entities: List[str]
    ) -> Dict[str, Dict]:
        """Fallback rule-based prediction"""
        
        predictions = {}
        
        for doc in documents:
            doc_id = doc.get("document_id")
            predictions[doc_id] = {
                "document_level": {},
                "section_level": {}
            }
            
            # Simple keyword matching
            doc_text = ""
            if "title" in doc:
                doc_text += doc["title"] + " "
            
            if "source_text" in doc:
                for section in doc["source_text"]:
                    doc_text += section.get("text", "") + " "
            
            doc_text_lower = doc_text.lower()
            
            # Document level
            for entity in entities:
                if entity.lower() in doc_text_lower:
                    # Calculate simple relevance score based on frequency
                    count = doc_text_lower.count(entity.lower())
                    score = min(1.0, count * 0.1)
                    predictions[doc_id]["document_level"][entity] = score
            
            # Section level
            if "source_text" in doc:
                for section in doc["source_text"]:
                    section_id = section.get("section_id", "unknown")
                    section_text = section.get("text", "").lower()
                    
                    section_predictions = {}
                    for entity in entities:
                        if entity.lower() in section_text:
                            count = section_text.count(entity.lower())
                            score = min(1.0, count * 0.15)
                            section_predictions[entity] = score
                    
                    if section_predictions:
                        predictions[doc_id]["section_level"][section_id] = section_predictions
        
        return predictions
    
    def export_predictions(self, predictions: Dict, filepath: str):
        """Export predictions to file"""
        
        # Convert to list format for easier processing
        results = []
        
        for doc_id, doc_predictions in predictions.items():
            # Document level
            for entity, confidence in doc_predictions["document_level"].items():
                results.append({
                    "document_id": doc_id,
                    "level": "document",
                    "section_id": None,
                    "entity": entity,
                    "confidence": confidence
                })
            
            # Section level
            for section_id, section_preds in doc_predictions["section_level"].items():
                for entity, confidence in section_preds.items():
                    results.append({
                        "document_id": doc_id,
                        "level": "section",
                        "section_id": section_id,
                        "entity": entity,
                        "confidence": confidence
                    })
        
        # Save as JSON
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Also save as CSV
        df = pd.DataFrame(results)
        csv_path = filepath.replace('.json', '.csv')
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Predictions saved to {filepath} and {csv_path}")