"""
Forbidden Shell Command Blocker Hook

Prevents execution of raw, unverified terminal shell commands outside 
the Python testing/validation framework.

Enforces Workspace Rule 4: Tool & Script Execution Boundaries.

This hook is triggered pre-execution on shell_execution tool use.
"""

import re
import sys
from typing import Dict, List, Any


def check_shell_authorization(command: str, authorized_patterns: List[str]) -> Dict[str, Any]:
    """
    Check if a shell command matches authorized execution patterns.
    
    Args:
        command: Full shell command to execute
        authorized_patterns: List of regex patterns for authorized commands
    
    Returns:
        dict with keys:
            - authorized: bool
            - message: str
            - matched_pattern: str or None
            - error: str (if not authorized)
    """
    
    result = {
        "authorized": False,
        "message": "",
        "matched_pattern": None,
        "error": None
    }
    
    if not command or not isinstance(command, str):
        result["error"] = "Invalid command: must be non-empty string"
        return result
    
    command_stripped = command.strip()
    
    # Check against authorized patterns
    for pattern in authorized_patterns:
        try:
            if re.match(pattern, command_stripped):
                result["authorized"] = True
                result["matched_pattern"] = pattern
                result["message"] = f"✓ Command authorized (matched pattern: {pattern})"
                return result
        except re.error as e:
            result["error"] = f"Invalid regex pattern: {pattern} ({str(e)})"
            return result
    
    # No matches - command is unauthorized
    result["error"] = (
        f"Unauthorized shell command blocked. "
        f"Only authorized patterns are allowed: {', '.join(authorized_patterns[:3])}... "
        f"Use Python scripts in src/ or tests/ instead."
    )
    return result


def validate_python_script_path(script_path: str) -> bool:
    """
    Validate that a Python script is in an authorized directory.
    
    Args:
        script_path: Path to Python script
    
    Returns:
        bool: True if path is authorized, False otherwise
    """
    
    authorized_dirs = [
        "src/analysis/",
        "src/hooks/",
        "src/schema/",
        "tests/",
        "notebooks/"
    ]
    
    normalized_path = script_path.replace("\\", "/").lower()
    
    for auth_dir in authorized_dirs:
        if normalized_path.startswith(auth_dir) or f"/{auth_dir}" in normalized_path:
            return True
    
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate shell command authorization")
    parser.add_argument("--command", required=True, help="Shell command to validate")
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=[
            r"^python (src/|tests/)",
            r"^jupyter notebook",
            r"^python -m pytest"
        ],
        help="Authorized command patterns (regex)"
    )
    
    args = parser.parse_args()
    
    result = check_shell_authorization(args.command, args.patterns)
    
    print(f"\nShell Command Authorization Check:")
    print(f"  Command: {args.command}")
    print(f"  Authorized: {result['authorized']}")
    print(f"  Message: {result['message']}")
    
    if result["error"]:
        print(f"  Error: {result['error']}")
        sys.exit(1)
    else:
        sys.exit(0)
