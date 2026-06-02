# Complete Pydantic Schema & Validation - Quick Start Guide

**Status**: ✅ All Files Created & Ready  
**Files Created**: 9 core files + 1 guide  
**Dependencies**: Pydantic 2.5.0 (added to requirements.txt)

---

## What Was Created

### 1. **Validation Script** (Entry Point)
```
tests/validate_pydantic_schema.py
```
**Usage**:
```bash
python tests/validate_pydantic_schema.py \
  --report-file data/reports/variant_report.json \
  --schema-version 1.0 \
  --halt-on-error true
```

### 2. **Schema Definitions**
```
src/schema/genomic_impact_models.py    → Reusable Pydantic models
src/schema/__init__.py                  → Package exports
```

**Import in your code**:
```python
from src.schema import VariantFunctionalImpactReport
```

### 3. **Hook Implementation Scripts**
```
src/hooks/validate_assembly_context.py      → Check hg38 assembly
src/hooks/validate_shell_execution.py       → Authorize shell commands
src/hooks/audit_logging.py                  → SHA256 fingerprinting
src/hooks/post_analysis_packaging.py        → Archive versioned reports
src/hooks/__init__.py                       → Package initialization
```

### 4. **Analysis Package**
```
src/analysis/__init__.py                 → For future analysis modules
```

---

## Key Features

### Strict Type Enforcement
- All floating-point scores bounded to [0.0, 1.0] with 4 decimal precision
- Expression deltas unbounded (typical range -5.0 to +5.0)
- Confidence metrics always 0.0–1.0
- Enums for categorical values (no free-form strings for risk/status)
- SHA256 validation (64-char hex only)

### Assembly Anchoring
- hg38 enforced at schema level (const validation)
- Cannot create report with different assembly
- Assembly context check hook pre-execution

### Auditability
- SHA256 fingerprinting of inputs
- ISO-8601 timestamps throughout
- Execution duration tracking
- Archive with 90-day retention policy

### Error Handling
- Detailed Pydantic validation errors
- Hook-triggered recovery
- Quarantine system for failed reports

---

## File Locations & Logs

```
Project Root
├── tests/validate_pydantic_schema.py
├── src/
│   ├── schema/
│   │   ├── genomic_impact_models.py
│   │   └── __init__.py
│   ├── hooks/
│   │   ├── validate_assembly_context.py
│   │   ├── validate_shell_execution.py
│   │   ├── audit_logging.py
│   │   ├── post_analysis_packaging.py
│   │   └── __init__.py
│   └── analysis/
│       └── __init__.py
├── logs/                                 (auto-created)
│   ├── input_audit.jsonl
│   ├── execution_trace.jsonl
│   ├── analysis_index.jsonl
│   └── archive_manifest.json
└── data/
    └── .quarantine/                      (auto-created)
        └── archive_YYYYMMDDHHMMSS_*.json
```

---

## Common Usage Patterns

### Pattern 1: Create and Validate a Report

```python
import json
from datetime import datetime
from src.schema import VariantFunctionalImpactReport, VariantReportMetadata
from src.schema import VariantInputMetadata, AuditMetadata, AssemblyContext

# Create report object
report = VariantFunctionalImpactReport(
    metadata=VariantReportMetadata(
        analysis_id="MY-ANALYSIS-001",
        variant_id="VAR-001",
        timestamp=datetime.utcnow(),
        assembly=AssemblyContext.HG38,
        schema_version="1.0"
    ),
    input=VariantInputMetadata(
        coordinate="chr17:43044295A>G",
        context_window_kb=1000
    ),
    results={
        "chromatin_impact": {
            "disruption_score": 0.75,
            "confidence": 0.88,
            "peak_proximity": "NEAR",
            "affected_track_count": 2
        },
        "expression_impact": {
            "delta_mean_log2fc": -1.2,
            "delta_max_log2fc": -1.8,
            "tissues_affected": ["heart", "brain"],
            "confidence": 0.82
        },
        "combined_risk_score": 0.68,
        "risk_category": "MODERATE_RISK",
        "validation_status": "VALID",
        "missing_tracks": []
    },
    audit=AuditMetadata(
        input_sha256="abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
        execution_duration_seconds=12,
        data_sources=["dnase_hg38", "gtex_v8"]
    )
)

# Serialize to JSON
json_str = report.model_dump_json(indent=2)

# Save to file
with open("data/reports/my_report.json", "w") as f:
    f.write(json_str)
```

### Pattern 2: Validate a Report File

```bash
python tests/validate_pydantic_schema.py \
  --report-file data/reports/my_report.json \
  --halt-on-error true
```

### Pattern 3: Check Assembly Context Before Analysis

```python
from src.hooks.validate_assembly_context import verify_hg38_assembly

result = verify_hg38_assembly("data/variants/input.vcf")
if result["valid"]:
    print(f"✓ Can proceed - assembly is {result['assembly']}")
    # Start analysis
else:
    print(f"✗ Block analysis - {result['error']}")
    # Abort
```

### Pattern 4: Log Analysis with Audit Trail

```python
from src.hooks.audit_logging import log_analysis_initiation
from datetime import datetime

audit_result = log_analysis_initiation(
    input_file="data/variants/sample.json",
    analysis_type="functional_track_disruption",
    timestamp=datetime.utcnow().isoformat() + "Z"
)

analysis_id = audit_result["analysis_id"]
print(f"Started: {analysis_id}")

# ... run analysis ...

from src.hooks.audit_logging import log_analysis_completion
log_analysis_completion(
    analysis_id=analysis_id,
    output_file="data/reports/output.json",
    execution_duration_seconds=15,
    status="SUCCESS"
)
```

### Pattern 5: Package and Archive Results

```python
from src.hooks.post_analysis_packaging import package_analysis_artifacts

pkg_result = package_analysis_artifacts(
    output_file="data/reports/output.json",
    analysis_id="BRCA1-VUS-001_20260602154656",
    timestamp=datetime.utcnow().isoformat() + "Z"
)

print(f"Archived: {pkg_result['archived_path']}")
```

---

## Pydantic Model Hierarchy

```
VariantFunctionalImpactReport (top-level)
├── metadata: VariantReportMetadata
│   ├── analysis_id: str
│   ├── variant_id: str
│   ├── timestamp: datetime
│   ├── assembly: AssemblyContext (enum: hg38)
│   └── schema_version: str
├── input: VariantInputMetadata
│   ├── coordinate: str (regex validated)
│   ├── context_window_kb: int (100-5000)
│   └── prediction_types: list[str]
├── results: dict
│   ├── chromatin_impact
│   │   ├── disruption_score: float [0.0-1.0]
│   │   ├── confidence: float [0.0-1.0]
│   │   ├── peak_proximity: enum (FAR|NEAR|OVERLAPPING)
│   │   └── affected_track_count: int ≥0
│   ├── expression_impact
│   │   ├── delta_mean_log2fc: float (unbounded)
│   │   ├── delta_max_log2fc: float (unbounded)
│   │   ├── tissues_affected: list[str] (min 1 item)
│   │   └── confidence: float [0.0-1.0]
│   ├── combined_risk_score: float [0.0-1.0]
│   ├── risk_category: str enum
│   ├── validation_status: str enum
│   └── missing_tracks: list[str]
└── audit: AuditMetadata
    ├── input_sha256: str (64-char hex)
    ├── execution_duration_seconds: int ≥0
    └── data_sources: list[str] (min 1 item)
```

---

## Validation Error Examples

### ❌ Invalid: Score out of bounds
```json
{"chromatin_impact": {"disruption_score": 1.5}}
```
**Error**: `Input should be a valid number in the range [0.0, 1.0]`

### ❌ Invalid: Wrong assembly
```json
{"metadata": {"assembly": "hg19"}}
```
**Error**: `Input should be 'hg38' [type=enum_value]`

### ❌ Invalid: Invalid coordinate
```json
{"input": {"coordinate": "invalid_format"}}
```
**Error**: `String should match pattern '^chr([1-9]...'`

### ✅ Valid
```json
{
  "chromatin_impact": {
    "disruption_score": 0.8700,
    "confidence": 0.9200,
    "peak_proximity": "OVERLAPPING",
    "affected_track_count": 3
  }
}
```

---

## Installation & Setup

### 1. Install Pydantic
```bash
pip install pydantic==2.5.0
```

Or from updated requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Test Validation Script
```bash
python tests/validate_pydantic_schema.py --help
```

### 3. Run a Quick Test
```bash
# Create a sample report and validate it
python -c "
from src.schema import VariantFunctionalImpactReport
from datetime import datetime
print('✓ Pydantic schema module imported successfully')
"
```

---

## Integration with Hooks

The hook scripts integrate with `.github/hooks/hooks.json`:

1. **Pre-Analysis**: `validate_assembly_context.py` verifies hg38
2. **Pre-Analysis**: `audit_logging.py` fingerprints input
3. **Post-Report**: `validate_pydantic_schema.py` validates schema
4. **Post-Report**: `post_analysis_packaging.py` archives report

See `WORKSPACE_CONFIG_MANIFEST.md` for hook configuration details.

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'pydantic'
**Solution**: `pip install pydantic==2.5.0`

### Issue: Validation fails with "Input should be a valid number"
**Cause**: Float value is out of bounds or wrong type  
**Solution**: Check that score is between 0.0 and 1.0

### Issue: "Assembly mismatch: file declares 'hg19'"
**Cause**: Input variant file is not hg38  
**Solution**: Convert or exclude non-hg38 files

### Issue: Coordinate validation fails
**Cause**: Invalid HGVS format  
**Solution**: Use format: `chrN:positionREF>ALT` (e.g., `chr17:43044295A>G`)

---

## Next Steps

1. **Generate test report** using Pattern 1 above
2. **Validate the report** using Pattern 2
3. **Integrate into analysis pipeline** (import VariantFunctionalImpactReport)
4. **Deploy hooks** (configure in `.github/hooks/hooks.json`)
5. **Monitor audit trails** (check `logs/` directory)

---

**Quick Reference**: All files are in production-ready state with zero placeholders. Start using immediately in your analysis pipeline.

