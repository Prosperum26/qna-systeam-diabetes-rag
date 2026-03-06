"""
Embedding wrapper module for converting text to vector embeddings.

This module provides a reusable Embedder class that:
- Loads a pre-trained embedding model from HuggingFace
- Converts text to vector embeddings
- Supports both single and batch embedding
- Applies vector normalization for cosine similarity
- Handles GPU/CPU device selection
"""

import torch
import numpy as np
from typing import List
from transformers import AutoTokenizer, AutoModel


class Embedder:
    """
    Wrapper for embedding text using a pre-trained transformer model.
    
    Attributes:
        model_name (str): HuggingFace model identifier
        device (str): Device to load model on ("cpu" or "cuda")
        normalize (bool): Whether to apply L2 normalization
        tokenizer: HuggingFace tokenizer
        model: HuggingFace transformer model
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu",
        normalize: bool = True,
    ) -> None:
        """
        Initialize the Embedder by loading model and tokenizer.
        
        Args:
            model_name: HuggingFace model ID. Defaults to multilingual MiniLM (384 dims).
            device: Computation device. Either "cpu" or "cuda". Defaults to "cpu".
            normalize: Whether to apply L2 normalization. Defaults to True.
        """
        self.model_name = model_name
        self.device = device
        self.normalize = normalize

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

        # Move model to device
        self.model = self.model.to(device)
        self.model.eval()  # Set to evaluation mode

    def _mean_pooling(
        self,
        model_output: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Apply mean pooling to model output, ignoring padding tokens.
        
        Formula: sum(token_embeddings * attention_mask) / sum(attention_mask)
        
        Args:
            model_output: Token embeddings from model [batch_size, seq_len, hidden_dim]
            attention_mask: Attention mask [batch_size, seq_len]
            
        Returns:
            Sentence embeddings [batch_size, hidden_dim]
        """
        # Expand attention mask to match token embeddings shape
        attention_mask_expanded = (
            attention_mask.unsqueeze(-1)
            .expand(model_output.shape)
            .float()
        )

        # Sum token embeddings, masked by attention
        sum_embeddings = torch.sum(
            model_output * attention_mask_expanded,
            dim=1,
        )

        # Count non-padding tokens per sentence
        sum_mask = attention_mask_expanded.sum(dim=1)
        sum_mask = torch.clamp(sum_mask, min=1e-9)  # Avoid division by zero

        # Compute mean
        mean_embeddings = sum_embeddings / sum_mask

        return mean_embeddings

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """
        Apply L2 normalization to a vector.
        
        Formula: vector / ||vector||
        
        Args:
            vector: Embedding vector
            
        Returns:
            Normalized vector with L2 norm = 1
        """
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector

    def embed(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Steps:
        1. Tokenize text
        2. Run model inference
        3. Apply mean pooling
        4. Normalize if enabled
        5. Return as Python list
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Inference
        with torch.no_grad():
            model_output = self.model(**inputs)

        # Mean pooling
        embeddings = self._mean_pooling(
            model_output.last_hidden_state,
            inputs["attention_mask"],
        )

        # Extract and convert to numpy
        embedding_np = embeddings[0].cpu().numpy()

        # Normalize
        if self.normalize:
            embedding_np = self._normalize(embedding_np)

        # Convert to list
        return embedding_np.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in a batch.
        
        Performs batch inference for better performance compared to
        embedding texts one-by-one.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not texts:
            return []

        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Batch inference
        with torch.no_grad():
            model_output = self.model(**inputs)

        # Mean pooling
        embeddings = self._mean_pooling(
            model_output.last_hidden_state,
            inputs["attention_mask"],
        )

        # Convert to numpy and normalize
        embeddings_np = embeddings.cpu().numpy()

        if self.normalize:
            embeddings_np = np.array(
                [self._normalize(emb) for emb in embeddings_np]
            )

        # Convert to list of lists
        return embeddings_np.tolist()
