# 🧬 AI-Native Functional Genomics & Variant Effect Predictor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.5-red)](https://docs.pydantic.dev/)
[![hg38 Reference](https://img.shields.io/badge/Assembly-hg38-green)](https://www.ncbi.nlm.nih.gov/grc/human/data)

An **AI-Native workspace** utilizing the **VS Code Copilot Agent Architecture** to transition genomic clinical variant analysis from static database lookups to **dynamic, track-perturbation forecasting** with cryptographic audit trails and type-safe guardrails.

---

## 🚀 The Paradigm Shift

Traditional variant calling isolates single mutations and flags unknown changes as **VUS (Variants of Uncertain Significance)**—creating biological dead ends. This architecture shifts the paradigm to **Functional Genomic Context Reasoning** (aligned with modern foundation models like Google DeepMind's AlphaGenome).

By analyzing a **1-Megabase (1Mb) sequence context** on the human `hg38` assembly, this system automatically maps **Single-Base Resolution Functional Predictions** across:
- **Chromatin Accessibility** (DNase hypersensitivity, ATAC-seq consensus peaks)
- **Expression Regulatory Deltas** (tissue-specific baselines, eQTL associations)
- **Composite Risk Scoring** (quantified disruption magnitude + confidence)

---

## 🛡️ Enterprise-Grade Guardrail Architecture

To completely eliminate **Large Language Model (LLM) hallucinations** and ensure clinical-grade data safety, this system enforces an immediate **Type-Safe Validation and Execution Layer**. The AI agent is entirely boxed into a deterministic, audit-logged environment.

```
┌─────────────────────────────────────────────────────────────────┐
│ User Input: VUS Coordinate (chr17:g.43044295A>G)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        [Pre-Execution Hook] ──→ Enforces Rigid hg38 Assembly Anchoring
                              ↓
        [Audit Logger]        ──→ SHA256 fingerprint input file
                              ↓
        [Genomic Agent Loop]  ──→ Analyzes 1Mb Track Perturbations
                              ↓
   [Post-Execution Validator] ──→ Pydantic Schema Validation
                                  (Blocks prose / free-form hallucinations)
                              ↓
   [Chromatin Score: 0.8700]
   [Expression Delta: -1.4500 log2fc]
   [Risk Category: HIGH_RISK]
   [Assembly: hg38] ✓
                              ↓
   [Cryptographic Hook]       ──→ Generates SHA256-Immutable JSONL Trace
                              ↓
   [Quarantine Archive]       ──→ Versions & 90-day retention
                              ↓
   ✅ Machine-Readable JSON Output (No Hallucinations)
```

### 🧱 Core Architecture Components

#### 1. **Custom Agent Persona** (`.github/agents/genomic-analyst.md`)
- Limits the AI's boundaries to a highly conservative clinical computational biologist
- Forbids unauthorized shell execution
- Requires Pydantic schema validation before output

#### 2. **Strict Pydantic Enforcer** (`tests/validate_pydantic_schema.py` — 19.9 KB)
- Forces all track calculations into **explicit floating-point numbers** with exact decimal precision
- Bounds categorical outcomes into strict `Enums`: `{LOW_RISK, MODERATE_RISK, HIGH_RISK}`
- Validates assembly context = `hg38` (const-level enforcement)

#### 3. **Cryptographic Audit Trail** (`src/hooks/`)
- **Assembly Verifier**: Checks VCF/JSON/BED files for `hg38` declaration pre-execution
- **Shell Authorizer**: Blocks raw commands; only permits authorized execution
- **Audit Logger**: SHA256-hashes input files, logs ISO-8601 timestamps
- **Artifact Packager**: Versions reports with analysis ID + timestamp

#### 4. **Model Context Protocol Pool** (`.vscode/mcp.json`)
- Type-safe JSON-Schema routing to genomic track databases
- Enforces strict method signatures + bounds checking

---

## 📂 Directory Structure

```
your-genomics-project/
├── .github/
│   ├── agents/genomic-analyst.md
│   ├── skills/predict-track-disruption/SKILL.md
│   ├── hooks/hooks.json
│   └── copilot-instructions.md
├── src/
│   ├── schema/genomic_impact_models.py
│   └── hooks/*.py
├── tests/validate_pydantic_schema.py
├── logs/                               # Auto-created by hooks
├── data/reports/ & .quarantine/       # Auto-created
└── PYDANTIC_QUICK_START.md
```

---

## 🏃 Quick Start & Verification

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Validate a Sample Report

```bash
python tests/validate_pydantic_schema.py \
  --report-file data/reports/example_report.json \
  --schema-version 1.0 \
  --halt-on-error true
```

### 3. See Type-Safety in Action

```bash
# Create a broken report (hallucinated data)
python -c "
import json
broken = {
    'metadata': {...},
    'results': {
        'chromatin_impact': {
            'disruption_score': 1.5  # ❌ OUT OF BOUNDS (max 1.0)
        }
    }
}
with open('data/reports/broken.json', 'w') as f:
    json.dump(broken, f)
"

# Validation FAILS - guardrails work
python tests/validate_pydantic_schema.py --report-file data/reports/broken.json
```

---

## 🔐 Security & Reproducibility

- **Assembly Anchoring:** hg38-only (const-level enforcement)
- **Cryptographic Audit Trails:** SHA256 + ISO-8601 logging
- **Type-Safe Output:** No prose allowed (Pydantic enums only)
- **90-Day Retention:** Versioned archives with compliance tracking

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **WORKSPACE_CONFIG_MANIFEST.md** | Complete architecture audit |
| **PYDANTIC_SCHEMA_IMPLEMENTATION.md** | Technical implementation guide |
| **PYDANTIC_QUICK_START.md** | Usage patterns & examples |

---

## 📜 License

MIT License — distributed for reproducible, secure computational biology infrastructure.

---

**Built with:** Python 3.11+ | Pydantic v2.5 | VS Code Copilot Architecture | hg38 Assembly
