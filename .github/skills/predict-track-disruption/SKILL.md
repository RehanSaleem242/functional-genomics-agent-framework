---
name: predict-track-disruption
description: Predict functional track disruptions for variants in 1Mb context windows
applyTo:
  - patterns: ["**/variant_*.json", "**/vus_*.vcf", "**/analysis_request_*.py"]
  - tags: ["genomics", "variant-analysis", "functional-prediction"]
invocationContext:
  - user_message_contains: ["track disruption", "functional impact", "chromatin", "expression delta", "VUS"]
  - tool_uses: ["grep_variant_files", "python_execution", "pydantic_validation"]
requiresApproval: true
---

# Predict Track Disruption Skill

**Activation Context**: Invoked when analyzing Variants of Uncertain Significance (VUS) for disruption of chromatin accessibility or gene expression regulatory tracks. Works exclusively within hg38 coordinate system.

---

## Biological Protocol: 1Mb Functional Context Analysis

### Phase 1: Sequence Context Acquisition

**Objective**: Establish genomic anchor point and extract flanking sequence window.

**Steps**:
1. Parse variant coordinate (HGVS format: `chr:g.positionREF>ALT`)
2. Validate coordinate against hg38 assembly reference
3. Define context boundaries:
   - Position start: `variant_position - 500000` bp
   - Position end: `variant_position + 500000` bp
   - Total window: 1,000,001 bp centered on variant
4. Query FASTA reference (`hg38.fasta` or indexed access via BioPython)
5. Extract flanking sequences and store in memory/temp file
6. Log sequence metadata: chromosome, start position, end position, sequence length

**Validation Gate**:
- Assert window size ≥ 1,000,000 bp
- Confirm all positions exist in hg38 (no scaffold/unknown regions without explicit flagging)
- Verify variant position is within bounds

---

### Phase 2: Functional Track Compilation

**Objective**: Aggregate chromatin accessibility and expression predictions for the 1Mb window.

**Sub-Step 2A: Chromatin Accessibility Track**

1. Query chromatin accessibility data sources (mock/simulated or real):
   - DNase hypersensitivity sites (DHS) annotations
   - ATAC-seq consensus peaks
   - Histone modification alignments (H3K27ac, H3K4me1, H3K4me3)
   
2. For each track, compute:
   - Base-by-base signal intensity (0–1 normalized scale)
   - Peak call boundaries (start, end, q-value)
   - Tissue/cell-type context (e.g., fibroblast, lymphocyte, neural)

3. Generate aggregated chromatin score:
   ```
   chromatin_disruption_score = 1.0 - (predicted_accessibility_with_variant / baseline_accessibility)
   ```
   - Range: 0 (no disruption) to 1 (complete loss)

4. If variant is within ±50bp of a peak boundary, flag as "HIGH_RISK_REGION"

**Sub-Step 2B: Expression Regulation Track**

1. Query expression prediction models:
   - Tissue-specific baseline expression (RPKM/TPM from GTEx or synthetic model)
   - Promoter/enhancer regulatory regions (±5kb from TSS, distal regulatory elements)
   - Expression Quantitative Trait Loci (eQTL) associations

2. For each tissue/cell type, compute:
   - Predicted expression level with variant
   - Predicted expression level without variant (wildtype baseline)
   - Log fold-change: `log2(exp_with_variant / exp_baseline)`

3. Aggregate across tissue contexts:
   - Mean expression delta (across all tissues)
   - Maximum absolute expression delta (tissue of greatest impact)
   - Tissue count with |delta| > 0.5 log fold-change

---

### Phase 3: Functional Impact Quantification

**Objective**: Map aggregated functional predictions to structured, machine-readable output.

**Steps**:

1. **Chromatin Impact Metrics**:
   - `chromatin_disruption_score`: float [0.0, 1.0]
   - `chromatin_confidence`: float [0.0, 1.0] (model confidence)
   - `peak_proximity_flag`: enum {FAR, NEAR, OVERLAPPING}
   - `affected_track_count`: int (number of disrupted chromatin marks)

2. **Expression Impact Metrics**:
   - `expression_delta_mean_log2fc`: float (log-fold change averaged across tissues)
   - `expression_delta_max_log2fc`: float (most extreme tissue effect)
   - `tissues_with_delta`: list of str (tissue names with |delta| > threshold)
   - `expression_confidence`: float [0.0, 1.0]

3. **Combined Pathogenicity Risk Score**:
   ```
   risk_score = (0.6 * chromatin_disruption_score + 0.4 * |expression_delta_mean_log2fc|) / 1.6
   ```
   - Normalized to [0.0, 1.0] scale
   - Values > 0.7 → HIGH_RISK
   - Values 0.4–0.7 → MODERATE_RISK
   - Values < 0.4 → LOW_RISK

4. **Validation Status**:
   - `schema_validation_status`: enum {VALID, INVALID_SCHEMA, DATA_GAP}
   - `missing_track_types`: list of str (tracks unavailable in this region)
   - `assembly_confirmed`: enum {hg38}

---

### Phase 4: Output Schema Generation

**Objective**: Serialize results into strict Pydantic-validated JSON.

**Pydantic Data Model Structure**:

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class PeakProximityFlag(str, Enum):
    FAR = "FAR"
    NEAR = "NEAR"
    OVERLAPPING = "OVERLAPPING"

class ValidationStatus(Enum):
    VALID = "VALID"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    DATA_GAP = "DATA_GAP"

class ChromatinImpact(BaseModel):
    disruption_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    peak_proximity: PeakProximityFlag
    affected_track_count: int = Field(..., ge=0)

class ExpressionImpact(BaseModel):
    delta_mean_log2fc: float
    delta_max_log2fc: float
    tissues_affected: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)

class VariantFunctionalImpactReport(BaseModel):
    variant_id: str
    coordinate: str
    assembly: str
    context_window_kb: int = 1000
    chromatin_impact: ChromatinImpact
    expression_impact: ExpressionImpact
    combined_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_category: str  # HIGH_RISK, MODERATE_RISK, LOW_RISK
    validation_status: ValidationStatus
    missing_tracks: List[str]
```

**Output Generation**:
1. Instantiate `VariantFunctionalImpactReport` with computed metrics
2. Validate against Pydantic schema (raises `ValidationError` on failure)
3. Serialize to JSON via `.model_dump_json(indent=2)`
4. Write to `/data/reports/{variant_id}_functional_impact.json`

---

### Phase 5: Quality Assurance & Error Handling

**Validation Checkpoints**:
1. All floating-point values within declared bounds (0–1 for scores, unconstrained for log-fold-change)
2. Tissue list is non-empty if expression_delta exists
3. Variant coordinate is a valid hg38 position
4. Assembly field = "hg38" (no cross-assembly contamination)

**Error Handling**:
- **Missing Functional Tracks**: Set confidence to 0.5, populate `missing_tracks` list, set status to DATA_GAP
- **Coordinate Validation Failure**: Abort analysis, raise `CoordinateError`, log to stderr
- **Pydantic Schema Mismatch**: Trigger hook → `python tests/validate_pydantic_schema.py`

---

## Execution Command

```bash
python src/analysis/predict_track_disruption.py \
  --variant-file <path_to_variant.json> \
  --assembly hg38 \
  --context-window 1000 \
  --output-dir data/reports/
```

**Input JSON Example**:
```json
{
  "variant_id": "BRCA1-VUS-001",
  "coordinate": "chr17:g.43044295A>G",
  "assembly": "hg38",
  "annotation": "Pathogenic_suspect"
}
```

---

## Integration with Workspace

- **Input Files**: `/data/variants/*.json`, `/data/variants/*.vcf`
- **Output Location**: `/data/reports/`
- **Validation Script**: `tests/validate_pydantic_schema.py`
- **Log Files**: `logs/track_disruption_*.log`
- **Reference Data**: `data/reference/hg38.fasta` (must exist before execution)

This skill operates exclusively within the hg38 assembly context and produces strict machine-readable outputs. All natural language interpretation is deferred to post-analysis clinical review stages.
