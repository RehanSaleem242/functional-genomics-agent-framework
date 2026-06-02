"""
Assembly Context Validation Hook

Validates that all input variant files declare hg38 assembly context.
Enforces Workspace Rule 1: Genomic Assembly Anchoring (Non-Negotiable).

This hook is triggered pre-execution on variant_file_reader tool use.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def verify_hg38_assembly(file_path: str, expected_assembly: str = "hg38") -> Dict[str, Any]:
    """
    Verify that a variant file declares hg38 assembly context.
    
    Args:
        file_path: Path to the variant input file (VCF, JSON, or BED)
        expected_assembly: Expected assembly version (default: "hg38")
    
    Returns:
        dict with keys:
            - valid: bool
            - assembly: str (detected or missing)
            - message: str
            - error: str (if validation failed)
    """
    
    result = {
        "valid": False,
        "assembly": None,
        "message": "",
        "error": None
    }
    
    # Check file exists
    if not Path(file_path).exists():
        result["error"] = f"File not found: {file_path}"
        return result
    
    detected_assembly = None
    file_ext = Path(file_path).suffix.lower()
    
    try:
        # === VCF FILE DETECTION ===
        if file_ext == ".vcf" or file_ext == ".gz":
            with open(file_path, "r") as f:
                for line in f:
                    if line.startswith("##assembly="):
                        detected_assembly = line.split("=")[1].strip().lower()
                        break
            
            if not detected_assembly:
                result["error"] = f"VCF file missing ##assembly metadata line"
                return result
        
        # === JSON FILE DETECTION ===
        elif file_ext == ".json":
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Look for assembly field at root level
            if "assembly" in data:
                detected_assembly = data["assembly"].lower()
            # Or nested in metadata
            elif "metadata" in data and isinstance(data["metadata"], dict):
                if "assembly" in data["metadata"]:
                    detected_assembly = data["metadata"]["assembly"].lower()
            
            if not detected_assembly:
                result["error"] = "JSON file missing assembly field in root or metadata"
                return result
        
        # === BED FILE DETECTION ===
        elif file_ext == ".bed":
            # BED files don't carry assembly metadata natively
            # Check for comment line at top
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#assembly="):
                    detected_assembly = first_line.split("=")[1].strip().lower()
                else:
                    # No assembly declaration - require user confirmation
                    result["error"] = "BED file does not declare assembly. Add comment line: #assembly=hg38"
                    return result
        
        else:
            result["error"] = f"Unsupported file format: {file_ext}"
            return result
        
        # === ASSEMBLY VALIDATION ===
        result["assembly"] = detected_assembly
        
        # Normalize assembly names
        assembly_normalized = detected_assembly.lower().replace("grch38", "hg38").replace("grch38.p14", "hg38")
        
        if assembly_normalized != expected_assembly:
            result["error"] = (
                f"Assembly mismatch: file declares '{detected_assembly}', "
                f"but workspace requires '{expected_assembly}'. "
                f"Cross-assembly analysis is prohibited."
            )
            return result
        
        result["valid"] = True
        result["message"] = f"✓ Assembly context verified: {detected_assembly}"
        return result
    
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON syntax: {str(e)}"
        return result
    except Exception as e:
        result["error"] = f"Error parsing file: {str(e)}"
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify hg38 assembly context in variant files")
    parser.add_argument("--file", required=True, help="Path to variant file")
    parser.add_argument("--assembly", default="hg38", help="Expected assembly (default: hg38)")
    
    args = parser.parse_args()
    
    result = verify_hg38_assembly(args.file, args.assembly)
    
    print(f"\nAssembly Validation Result:")
    print(f"  File: {args.file}")
    print(f"  Valid: {result['valid']}")
    print(f"  Detected Assembly: {result['assembly']}")
    print(f"  Message: {result['message']}")
    
    if result["error"]:
        print(f"  Error: {result['error']}")
        sys.exit(1)
    else:
        sys.exit(0)
