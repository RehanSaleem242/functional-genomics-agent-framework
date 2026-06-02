"""
Utility functions for fetching and processing NCBI bacterial data
"""

from Bio import Entrez, SeqIO
from tqdm import tqdm
import os
from typing import List, Dict, Optional


def set_ncbi_email(email: str) -> None:
    """Set NCBI Entrez email (required for NCBI API access)"""
    Entrez.email = email
    print(f"NCBI Entrez email set to: {email}")


def fetch_bacterial_genome(accession: str, output_dir: str = "./data") -> str:
    """
    Fetch a bacterial genome from NCBI by accession ID
    
    Args:
        accession: GenBank accession ID (e.g., 'NC_000913')
        output_dir: Directory to save the FASTA file
    
    Returns:
        Path to the downloaded FASTA file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        handle = Entrez.efetch(db="nucleotide", id=accession, rettype="fasta", retmode="text")
        fasta_content = handle.read()
        handle.close()
        
        output_file = os.path.join(output_dir, f"{accession}.fasta")
        with open(output_file, 'w') as f:
            f.write(fasta_content)
        
        print(f"Downloaded {accession} to {output_file}")
        return output_file
    except Exception as e:
        print(f"Error fetching {accession}: {str(e)}")
        return None


def fetch_multiple_genomes(accessions: List[str], output_dir: str = "./data") -> Dict[str, str]:
    """
    Fetch multiple bacterial genomes from NCBI
    
    Args:
        accessions: List of GenBank accession IDs
        output_dir: Directory to save FASTA files
    
    Returns:
        Dictionary mapping accession IDs to file paths
    """
    results = {}
    for accession in tqdm(accessions, desc="Fetching genomes"):
        file_path = fetch_bacterial_genome(accession, output_dir)
        if file_path:
            results[accession] = file_path
    
    return results


def read_fasta_sequences(fasta_file: str) -> List[Dict]:
    """
    Read sequences from a FASTA file
    
    Args:
        fasta_file: Path to FASTA file
    
    Returns:
        List of dictionaries with sequence metadata
    """
    sequences = []
    for record in SeqIO.parse(fasta_file, "fasta"):
        sequences.append({
            'id': record.id,
            'description': record.description,
            'sequence': str(record.seq),
            'length': len(record.seq)
        })
    
    return sequences


def filter_sequences_by_length(sequences: List[Dict], min_length: int, max_length: Optional[int] = None) -> List[Dict]:
    """
    Filter sequences by length
    
    Args:
        sequences: List of sequence dictionaries
        min_length: Minimum sequence length
        max_length: Maximum sequence length (None for no upper limit)
    
    Returns:
        Filtered list of sequences
    """
    filtered = []
    for seq in sequences:
        if seq['length'] >= min_length:
            if max_length is None or seq['length'] <= max_length:
                filtered.append(seq)
    
    return filtered


def truncate_sequences(sequences: List[Dict], max_length: int) -> List[Dict]:
    """
    Truncate sequences to a maximum length (useful for model input)
    
    Args:
        sequences: List of sequence dictionaries
        max_length: Maximum length to truncate to
    
    Returns:
        List of truncated sequences
    """
    truncated = []
    for seq in sequences:
        truncated_seq = seq.copy()
        if seq['length'] > max_length:
            truncated_seq['sequence'] = seq['sequence'][:max_length]
            truncated_seq['length'] = max_length
            truncated_seq['truncated'] = True
        else:
            truncated_seq['truncated'] = False
        truncated.append(truncated_seq)
    
    return truncated
