"""
Post-Analysis Artifact Generation & Versioning Hook

After successful analysis, generates versioned report artifacts and updates 
audit records. Manages report archival and index maintenance.

This hook is triggered post-execution on variant_analysis_executor tool use.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def package_analysis_artifacts(
    output_file: str,
    analysis_id: str,
    timestamp: str,
    archive_dir: str = "data/.quarantine",
    index_file: str = "logs/analysis_index.jsonl"
) -> Dict[str, Any]:
    """
    Package analysis artifacts and create versioned archives.
    
    Args:
        output_file: Path to generated report file
        analysis_id: Unique analysis identifier
        timestamp: ISO-8601 completion timestamp
        archive_dir: Directory for archiving reports (default: data/.quarantine)
        index_file: Path to analysis index file
    
    Returns:
        dict with keys:
            - success: bool
            - archived_path: str (path to archived report)
            - index_updated: bool
            - error: str (if any)
    """
    
    result = {
        "success": False,
        "archived_path": None,
        "index_updated": False,
        "error": None
    }
    
    try:
        # === STEP 1: VERIFY OUTPUT FILE ===
        output_path = Path(output_file)
        if not output_path.exists():
            result["error"] = f"Output file not found: {output_file}"
            return result
        
        # === STEP 2: CREATE ARCHIVE DIRECTORY ===
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # === STEP 3: VERSION AND ARCHIVE REPORT ===
        timestamp_clean = timestamp.replace(":", "").replace("-", "").replace("T", "")[:14]
        archive_filename = f"{analysis_id}_{timestamp_clean}.json"
        archived_full_path = archive_path / archive_filename
        
        # Copy report to archive
        shutil.copy2(output_path, archived_full_path)
        result["archived_path"] = str(archived_full_path)
        
        # === STEP 4: UPDATE ANALYSIS INDEX ===
        index_path = Path(index_file)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        index_entry = {
            "analysis_id": analysis_id,
            "original_report": str(output_file),
            "archived_report": str(archived_full_path),
            "timestamp_archived": datetime.utcnow().isoformat() + "Z",
            "archive_timestamp": timestamp_clean
        }
        
        with open(index_path, "a") as f:
            f.write(json.dumps(index_entry) + "\n")
        
        result["index_updated"] = True
        result["success"] = True
        
        return result
    
    except Exception as e:
        result["error"] = f"Error packaging artifacts: {str(e)}"
        return result


def calculate_retention_expiry(
    archive_timestamp: str,
    retention_days: int = 90
) -> str:
    """
    Calculate expiry date for archived report based on retention policy.
    
    Args:
        archive_timestamp: ISO-8601 timestamp when archived
        retention_days: Number of days to retain (default: 90)
    
    Returns:
        str: ISO-8601 expiry date
    """
    
    from datetime import timedelta
    
    archived_dt = datetime.fromisoformat(archive_timestamp.replace("Z", "+00:00"))
    expiry_dt = archived_dt + timedelta(days=retention_days)
    
    return expiry_dt.isoformat() + "Z"


def generate_archive_manifest(
    archive_dir: str = "data/.quarantine",
    manifest_file: str = "logs/archive_manifest.json"
) -> Dict[str, Any]:
    """
    Generate manifest of all archived reports with retention tracking.
    
    Args:
        archive_dir: Directory containing archived reports
        manifest_file: Path to write manifest
    
    Returns:
        dict with keys:
            - success: bool
            - manifest_count: int (number of archived reports)
            - error: str (if any)
    """
    
    result = {
        "success": False,
        "manifest_count": 0,
        "error": None
    }
    
    try:
        archive_path = Path(archive_dir)
        if not archive_path.exists():
            result["error"] = f"Archive directory not found: {archive_dir}"
            return result
        
        # Collect all archived reports
        manifest_entries = []
        for report_file in archive_path.glob("*.json"):
            entry = {
                "filename": report_file.name,
                "filepath": str(report_file),
                "size_bytes": report_file.stat().st_size,
                "modified_timestamp": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat() + "Z",
                "retention_expiry": calculate_retention_expiry(
                    datetime.fromtimestamp(report_file.stat().st_mtime).isoformat() + "Z"
                )
            }
            manifest_entries.append(entry)
        
        result["manifest_count"] = len(manifest_entries)
        
        # Write manifest
        manifest_path = Path(manifest_file)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_entries, f, indent=2)
        
        result["success"] = True
        return result
    
    except Exception as e:
        result["error"] = f"Error generating archive manifest: {str(e)}"
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Package analysis artifacts and manage archival")
    parser.add_argument("--output-file", required=True, help="Path to generated report")
    parser.add_argument("--analysis-id", required=True, help="Unique analysis ID")
    parser.add_argument("--timestamp", required=True, help="ISO-8601 completion timestamp")
    parser.add_argument("--archive-dir", default="data/.quarantine", help="Archive directory")
    parser.add_argument("--index-file", default="logs/analysis_index.jsonl", help="Index file")
    
    args = parser.parse_args()
    
    result = package_analysis_artifacts(
        args.output_file,
        args.analysis_id,
        args.timestamp,
        args.archive_dir,
        args.index_file
    )
    
    print(f"\nPost-Analysis Artifact Packaging:")
    print(f"  Analysis ID: {args.analysis_id}")
    print(f"  Output File: {args.output_file}")
    print(f"  Archived: {result['archived_path']}")
    print(f"  Index Updated: {result['index_updated']}")
    print(f"  Success: {result['success']}")
    
    if result["error"]:
        print(f"  Error: {result['error']}")
        import sys
        sys.exit(1)
