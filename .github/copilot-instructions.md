# AI-Native Functional Genomics Workspace: Copilot Instructions

## Workspace Mandate

This workspace is engineered for computational prediction of functional track disruptions in Variants of Uncertain Significance (VUS) using AI-driven analysis. All AI interactions must adhere to strict clinical-grade data integrity and assembly anchoring requirements.

---

## RULE 1: Genomic Assembly Anchoring (Non-Negotiable)

### Primary Rule
**All genomic operations must anchor exclusively to the human hg38 assembly reference.**

### Enforcement
- Every variant coordinate must be normalized to hg38 (GRCh38.p14 build)
- Cross-species coordinate mixing is strictly prohibited
- Alternative human assemblies (hg19/GRCh37, CHM13, T2T-CHM13) require explicit user acknowledgment and separate isolated analysis sessions
- No implicit coordinate liftover without user consent

### Implementation
1. Validate assembly context before any variant processing:
   ```
   if assembly != "hg38":
       raise AssemblyMismatchError(f"Expected hg38, received {assembly}")
   ```

2. Log all coordinate sources:
   ```
   [2026-06-02 15:46:56] ASSEMBLY_CONTEXT: hg38 confirmed
   [2026-06-02 15:46:57] VARIANT_PARSED: chr17:43044295A>G (hg38 reference)
   ```

3. Reject variant files with ambiguous assembly metadata
4. Flag any cross-assembly ambiguities detected in input VCF/BED files

### Consequences of Violation
- Immediate analysis termination
- Report generation blocked
- Error logged to `logs/assembly_violations.log`
- User notification: "Assembly mismatch detected. Only hg38 is permitted in this workspace."

---

## RULE 2: Strict Data Type Output Enforcement (Machine-Readable Only)

### Primary Rule
**Every single output assessing a variant's biological impact must be rendered as a strict data type (float, integer, categorical enum) mapped to an analytical schema. Natural language "walls of text," subjective hand-waving summaries, or clinical commentary are prohibited.**

### Prohibited Output Formats
❌ ~~"This variant looks like it might disrupt a regulatory region based on sequence homology patterns"~~

❌ ~~"The variant is interesting because it's near an important gene"~~

❌ ~~"Clinically, this could be pathogenic if the protein function is affected"~~

### Mandatory Output Formats
✅ 
```json
{
  "variant_id": "BRCA1-VUS-001",
  "chromatin_disruption_score": 0.87,
  "chromatin_disruption_confidence": 0.92,
  "expression_delta_mean_log2fc": -1.45,
  "expression_confidence": 0.78,
  "combined_risk_score": 0.71,
  "risk_category": "HIGH_RISK",
  "validation_status": "VALID"
}
```

### Data Type Requirements

#### Floating-Point Metrics (4 decimal place precision)
- **Disruption Scores**: [0.0000, 1.0000] (0 = no disruption, 1 = complete loss)
- **Confidence Metrics**: [0.0000, 1.0000] (model confidence)
- **Expression Delta (log-fold-change)**: (-∞, +∞), typically [-5.0, +5.0] for biological systems
- **Risk Scores**: [0.0000, 1.0000] (composite pathogenicity metric)

#### Integer Metrics
- **Affected Track Count**: [0, ∞) (number of disrupted chromatin/expression marks)
- **Tissues Affected**: int count or list membership
- **Context Window**: 1000 (always, unless explicitly changed)

#### Categorical/Enum Metrics
```
RiskCategory: "LOW_RISK" | "MODERATE_RISK" | "HIGH_RISK"
ValidationStatus: "VALID" | "INVALID_SCHEMA" | "DATA_GAP"
AssemblyContext: "hg38"
PeakProximity: "FAR" | "NEAR" | "OVERLAPPING"
```

#### Structured Collections
- **Tissues Affected**: `["heart", "brain", "liver"]` (strict list, no prose)
- **Missing Tracks**: `["H3K27ac", "eQTL_data"]` (enum list only)
- **Confidence Intervals**: `{"lower": 0.65, "upper": 0.92}` (tuple or dict, no ranges like "~0.8")

### Validation Mechanism
1. All outputs validated against Pydantic schema at generation time
2. Schema validation failure → auto-trigger: `python tests/validate_pydantic_schema.py`
3. Generation of non-compliant output → task rejection with error message
4. Natural language summaries deferred to post-analysis clinical review (outside this workspace)

### Schema Definition Location
- Primary: `src/schema/genomic_impact_models.py` (Pydantic BaseModel definitions)
- Validation: `tests/validate_pydantic_schema.py` (enforces type compliance)

---

## RULE 3: Data Integrity & Auditability

### Requirement
All analysis operations must be fully auditable and reproducible.

### Implementation
1. **Immutable Input Logging**
   - Every input file fingerprinted (SHA256) at ingestion
   - Timestamp recorded: `[ISO-8601 datetime]`
   - Store in `logs/input_audit.jsonl`

2. **Intermediate State Tracking**
   - Functional track queries logged with result counts
   - Coordinate transformations (if any) logged step-by-step
   - File in `logs/execution_trace.jsonl`

3. **Output Versioning**
   - All reports tagged with analysis timestamp
   - Version identifier in JSON: `"analysis_timestamp": "2026-06-02T15:46:56Z"`
   - Retain in `/data/reports/archive/` for ≥90 days

### Audit Format
```json
{
  "analysis_id": "BRCA1-VUS-001_20260602154656",
  "input_file": "variants/brca1_vus.json",
  "input_sha256": "4a3f9d8e2c1b7a5f9e3c2b1a0f9e8d7c",
  "assembly_context": "hg38",
  "timestamp_start": "2026-06-02T15:46:56Z",
  "timestamp_end": "2026-06-02T15:47:12Z",
  "execution_status": "SUCCESS",
  "output_file": "reports/BRCA1-VUS-001_functional_impact.json"
}
```

---

## RULE 4: Tool & Script Execution Boundaries

### Authorized Execution Contexts
✅ Python scripts in `src/analysis/`, `src/schema/`, `tests/`
✅ Jupyter notebooks in `notebooks/` (analysis-only)
✅ Pydantic validation via `tests/validate_pydantic_schema.py`
✅ Reference data queries via BioPython/pysam (read-only)

### Strictly Forbidden
❌ Raw shell commands (bash, PowerShell, CMD) without explicit user approval
❌ Modification of production environment or deployment configs
❌ Installation of arbitrary pip packages without reviewing `requirements.txt`
❌ Writing to directories outside `/data/`, `/logs/`, `/notebooks/`

### Violation Handling
If AI agent attempts unauthorized shell execution:
1. Halt execution immediately
2. Log violation to `logs/security_violations.log`
3. Notify user: "Unauthorized shell command blocked"
4. Require explicit approval to proceed

---

## RULE 5: Reference Assembly Integrity

### Requirement
Maintain strict hg38 reference data consistency.

### Implementation
- Reference FASTA file: `data/reference/hg38.fasta` (must be indexed with `.fai`)
- Annotation files (BED, GTF) must be hg38-aligned
- Track databases (chromatin, expression) must carry hg38 metadata
- Validation at import: check for GRCh38 identifiers

### Coordinate Validation Schema
```python
def validate_hg38_coordinate(chrom: str, pos: int) -> bool:
    valid_chroms = {f"chr{i}" for i in range(1, 23)} | {"chrX", "chrY", "chrM"}
    if chrom not in valid_chroms:
        raise ValueError(f"Invalid chromosome: {chrom}")
    if not (1 <= pos <= 3_000_000_000):
        raise ValueError(f"Position {pos} out of human genome bounds")
    return True
```

---

## RULE 6: Variant File Format Standards

### Accepted Input Formats
- **VCF 4.2+**: Must include `##assembly=GRCh38` metadata line
- **BED6**: Must have hg38-aligned coordinates; recommend adding assembly column
- **JSON**: Custom variant schema (see `src/schema/variant_input_schema.py`)

### Validation on Import
1. Parse format, extract assembly context
2. Assert assembly = hg38
3. Validate all coordinates within bounds
4. Check for missing required fields (e.g., REF, ALT in VCF)
5. Log any records with quality flags or missing data

---

## RULE 7: Confidence & Uncertainty Quantification

### Requirement
All predictions must include confidence/uncertainty metrics.

### Confidence Scale (0.0–1.0)
- **0.90–1.00**: High confidence (model fully trained on this region, rich data)
- **0.70–0.89**: Moderate confidence (adequate training data, some track gaps)
- **0.50–0.69**: Low confidence (sparse data or model uncertainty)
- **< 0.50**: Very low confidence; flag as potential DATA_GAP

### Data Gap Handling
If any functional track is unavailable:
1. Set confidence for that metric to 0.5
2. Add track name to `missing_tracks` list
3. Set `validation_status` to "DATA_GAP"
4. Proceed with analysis using available data (do not abort)

---

## RULE 8: Report Structure (Mandatory JSON Schema)

All variant impact reports must conform to this structure:

```json
{
  "metadata": {
    "analysis_id": "string",
    "variant_id": "string",
    "timestamp": "ISO-8601 datetime",
    "assembly": "hg38",
    "schema_version": "1.0"
  },
  "input": {
    "coordinate": "chr:positionREF>ALT",
    "context_window_kb": 1000,
    "prediction_types": ["chromatin_accessibility", "expression_delta"]
  },
  "results": {
    "chromatin_impact": {
      "disruption_score": 0.87,
      "confidence": 0.92,
      "peak_proximity": "OVERLAPPING",
      "affected_track_count": 3
    },
    "expression_impact": {
      "delta_mean_log2fc": -1.45,
      "delta_max_log2fc": -2.30,
      "tissues_affected": ["heart", "brain"],
      "confidence": 0.78
    },
    "combined_risk_score": 0.71,
    "risk_category": "HIGH_RISK",
    "validation_status": "VALID",
    "missing_tracks": []
  },
  "audit": {
    "input_sha256": "hex-string",
    "execution_duration_seconds": 16,
    "data_sources": ["dnase_hg38", "gtex_expression_v8"]
  }
}
```

---

## Summary: Three Pillars of This Workspace

| Pillar | Rule |
|--------|------|
| **Assembly Integrity** | hg38-only. No cross-assembly contamination. |
| **Data Type Strictness** | Numeric/enum outputs only. No natural language impact summaries. |
| **Auditability** | Every analysis logged, fingerprinted, timestamped, reproducible. |

---

## Activation Context

These instructions are **always active** for:
- All Python script execution in `src/`, `tests/`
- All Jupyter notebook analysis in `notebooks/`
- All AI-agent variant analysis requests
- All data output to `/data/reports/`

**Exception**: Documentation files and non-analytical README content may contain explanatory prose.

---

**Last Updated**: 2026-06-02
**Schema Version**: 1.0
**Assembly Version**: hg38 (GRCh38.p14)
