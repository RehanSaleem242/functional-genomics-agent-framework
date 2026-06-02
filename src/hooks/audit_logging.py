"""
Data Integrity & Audit Trail Logger Hook

Logs all analysis operations with input fingerprints, timestamps, and execution 
traces for auditability and reproducibility.

Enforces Workspace Rule 3: Data Integrity & Auditability.

This hook is triggered pre-execution on variant_analysis_executor tool use.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def log_analysis_initiation(
    input_file: str,
    analysis_type: str,
    timestamp: str,
    log_dir: str = "logs"
) -> Dict[str, Any]:
    """
    Log the initiation of an analysis with input fingerprinting.
    
    Args:
        input_file: Path to input variant file
        analysis_type: Type of analysis being performed
        timestamp: ISO-8601 timestamp of analysis start
        log_dir: Directory for audit logs (default: logs)
    
    Returns:
        dict with keys:
            - success: bool
            - analysis_id: str
            - input_sha256: str
            - audit_log_path: str
            - error: str (if any)
    """
    
    result = {
        "success": False,
        "analysis_id": None,
        "input_sha256": None,
        "audit_log_path": None,
        "error": None
    }
    
    try:
        # === STEP 1: CHECK INPUT FILE ===
        if not Path(input_file).exists():
            result["error"] = f"Input file not found: {input_file}"
            return result
        
        # === STEP 2: COMPUTE SHA256 FINGERPRINT ===
        sha256_hash = hashlib.sha256()
        with open(input_file, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        
        input_sha256 = sha256_hash.hexdigest()
        result["input_sha256"] = input_sha256
        
        # === STEP 3: GENERATE ANALYSIS ID ===
        # Format: VARIANTID_TIMESTAMP_HASH[:8]
        timestamp_clean = timestamp.replace(":", "").replace("-", "").replace("T", "")[:14]
        analysis_id = f"analysis_{timestamp_clean}_{input_sha256[:8]}"
        result["analysis_id"] = analysis_id
        
        # === STEP 4: CREATE AUDIT LOG ENTRY ===
        audit_entry = {
            "analysis_id": analysis_id,
            "input_file": str(input_file),
            "input_sha256": input_sha256,
            "analysis_type": analysis_type,
            "timestamp_start": timestamp,
            "log_entry_created": datetime.utcnow().isoformat() + "Z",
            "status": "INITIATED"
        }
        
        # === STEP 5: WRITE TO AUDIT LOG ===
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        
        audit_log_path = log_dir_path / "input_audit.jsonl"
        
        with open(audit_log_path, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
        
        result["audit_log_path"] = str(audit_log_path)
        result["success"] = True
        
        return result
    
    except Exception as e:
        result["error"] = f"Error logging analysis initiation: {str(e)}"
        return result


def log_analysis_completion(
    analysis_id: str,
    output_file: str,
    execution_duration_seconds: int,
    status: str = "SUCCESS",
    log_dir: str = "logs"
) -> Dict[str, Any]:
    """
    Log the completion of an analysis.
    
    Args:
        analysis_id: Unique analysis identifier
        output_file: Path to generated output report
        execution_duration_seconds: Total execution time
        status: Completion status (SUCCESS, FAILED, etc.)
        log_dir: Directory for audit logs (default: logs)
    
    Returns:
        dict with keys:
            - success: bool
            - error: str (if any)
    """
    
    result = {
        "success": False,
        "error": None
    }
    
    try:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        
        completion_entry = {
            "analysis_id": analysis_id,
            "output_file": str(output_file),
            "execution_duration_seconds": execution_duration_seconds,
            "timestamp_end": datetime.utcnow().isoformat() + "Z",
            "status": status
        }
        
        execution_trace_path = log_dir_path / "execution_trace.jsonl"
        
        with open(execution_trace_path, "a") as f:
            f.write(json.dumps(completion_entry) + "\n")
        
        result["success"] = True
        return result
    
    except Exception as e:
        result["error"] = f"Error logging analysis completion: {str(e)}"
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Log analysis initiation with audit trail")
    parser.add_argument("--input-file", required=True, help="Path to input variant file")
    parser.add_argument("--analysis-type", required=True, help="Type of analysis")
    parser.add_argument("--timestamp", required=True, help="ISO-8601 timestamp")
    parser.add_argument("--log-dir", default="logs", help="Log directory (default: logs)")
    
    args = parser.parse_args()
    
    result = log_analysis_initiation(
        args.input_file,
        args.analysis_type,
        args.timestamp,
        args.log_dir
    )
    
    print(f"\nAnalysis Audit Logging:")
    print(f"  Input File: {args.input_file}")
    print(f"  Analysis ID: {result['analysis_id']}")
    print(f"  SHA256: {result['input_sha256']}")
    print(f"  Audit Log: {result['audit_log_path']}")
    print(f"  Success: {result['success']}")
    
    if result["error"]:
        print(f"  Error: {result['error']}")
        import sys
        sys.exit(1)
