"""
Utility functions for loading and running mamba models
"""

import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Optional, Tuple
import numpy as np


def load_mamba_model(model_name: str, device: Optional[str] = None):
    """
    Load a mamba model from Hugging Face hub
    
    Args:
        model_name: Model identifier (e.g., 'state-spaces/mamba-130m')
        device: Device to load model on ('cpu', 'cuda', or None for auto-detect)
    
    Returns:
        Tuple of (model, tokenizer)
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"Loading model: {model_name}")
    print(f"Using device: {device}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name).to(device)
        print(f"Model loaded successfully!")
        return model, tokenizer, device
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None, None, None


def tokenize_sequences(sequences: List[str], tokenizer, max_length: int = 512) -> Dict:
    """
    Tokenize sequences for model input
    
    Args:
        sequences: List of sequence strings
        tokenizer: Tokenizer from the model
        max_length: Maximum sequence length for tokenization
    
    Returns:
        Dictionary with tokenized inputs
    """
    encodings = tokenizer(
        sequences,
        max_length=max_length,
        padding=True,
        truncation=True,
        return_tensors='pt'
    )
    
    return encodings


def get_sequence_embeddings(
    sequences: List[str],
    model,
    tokenizer,
    device: str = 'cpu',
    batch_size: int = 32,
    max_length: int = 512
) -> np.ndarray:
    """
    Get embeddings for sequences from the mamba model
    
    Args:
        sequences: List of sequence strings
        model: Loaded mamba model
        tokenizer: Model tokenizer
        device: Device to run model on
        batch_size: Batch size for processing
        max_length: Maximum sequence length
    
    Returns:
        Array of embeddings
    """
    embeddings = []
    model.eval()
    
    with torch.no_grad():
        for i in range(0, len(sequences), batch_size):
            batch_sequences = sequences[i:i+batch_size]
            encodings = tokenize_sequences(batch_sequences, tokenizer, max_length)
            
            # Move to device
            input_ids = encodings['input_ids'].to(device)
            attention_mask = encodings['attention_mask'].to(device)
            
            # Get model outputs
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
            
            # Extract last hidden state and pool (mean pooling)
            last_hidden = outputs.last_hidden_state.cpu()
            batch_embeddings = last_hidden.mean(dim=1).numpy()
            
            embeddings.append(batch_embeddings)
    
    return np.vstack(embeddings)


def compute_sequence_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Cosine similarity score (0-1)
    """
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Reshape if needed
    if embedding1.ndim == 1:
        embedding1 = embedding1.reshape(1, -1)
    if embedding2.ndim == 1:
        embedding2 = embedding2.reshape(1, -1)
    
    similarity = cosine_similarity(embedding1, embedding2)[0, 0]
    return float(similarity)


def compare_pangenome_sequences(
    sequences: List[Dict],
    model,
    tokenizer,
    device: str = 'cpu'
) -> Dict:
    """
    Compare sequences within a pangenome
    
    Args:
        sequences: List of sequence dictionaries with 'id' and 'sequence' keys
        model: Loaded mamba model
        tokenizer: Model tokenizer
        device: Device to run model on
    
    Returns:
        Dictionary with comparison results
    """
    sequence_strings = [seq['sequence'] for seq in sequences]
    sequence_ids = [seq['id'] for seq in sequences]
    
    # Get embeddings
    embeddings = get_sequence_embeddings(
        sequence_strings,
        model,
        tokenizer,
        device=device
    )
    
    # Compute pairwise similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(embeddings)
    
    return {
        'sequence_ids': sequence_ids,
        'embeddings': embeddings,
        'similarity_matrix': similarity_matrix,
        'num_sequences': len(sequences)
    }
