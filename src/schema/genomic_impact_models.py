"""
Genomic Impact Data Models - Pydantic Schemas

This module exports all Pydantic models for variant functional impact analysis.
These models enforce strict data types and workspace Rule 2 (machine-readable output only).

Import these models in analysis scripts to generate and validate reports.
"""

from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Re-export all models from tests module for convenience
# In production, these would be centralized in a single location

class PeakProximityFlag(str, Enum):
    FAR = "FAR"
    NEAR = "NEAR"
    OVERLAPPING = "OVERLAPPING"


class RiskCategory(str, Enum):
    LOW_RISK = "LOW_RISK"
    MODERATE_RISK = "MODERATE_RISK"
    HIGH_RISK = "HIGH_RISK"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    DATA_GAP = "DATA_GAP"


class AssemblyContext(str, Enum):
    HG38 = "hg38"


class ChromatinImpact(BaseModel):
    """Chromatin accessibility disruption metrics."""
    
    disruption_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    peak_proximity: PeakProximityFlag
    affected_track_count: int = Field(..., ge=0)


class ExpressionImpact(BaseModel):
    """Gene expression disruption metrics."""
    
    delta_mean_log2fc: float
    delta_max_log2fc: float
    tissues_affected: List[str] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


class AuditMetadata(BaseModel):
    """Audit trail metadata."""
    
    input_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    execution_duration_seconds: int = Field(..., ge=0)
    data_sources: List[str] = Field(..., min_length=1)


class VariantReportMetadata(BaseModel):
    """Report metadata."""
    
    analysis_id: str = Field(..., min_length=5, max_length=100)
    variant_id: str = Field(..., min_length=3, max_length=100)
    timestamp: datetime
    assembly: AssemblyContext = AssemblyContext.HG38
    schema_version: str = "1.0"


class VariantInputMetadata(BaseModel):
    """Input analysis parameters."""
    
    coordinate: str = Field(
        ...,
        pattern=r"^chr([1-9]|[12][0-9]|3[0-2]|X|Y|M):[0-9]+[ATCG]>[ATCG]$"
    )
    context_window_kb: int = Field(default=1000, ge=100, le=5000)
    prediction_types: List[str] = Field(
        default=["chromatin_accessibility", "expression_delta"]
    )


class VariantFunctionalImpactReport(BaseModel):
    """Top-level variant functional impact report."""
    
    metadata: VariantReportMetadata
    input: VariantInputMetadata
    results: dict
    audit: AuditMetadata


__all__ = [
    "PeakProximityFlag",
    "RiskCategory",
    "ValidationStatus",
    "AssemblyContext",
    "ChromatinImpact",
    "ExpressionImpact",
    "AuditMetadata",
    "VariantReportMetadata",
    "VariantInputMetadata",
    "VariantFunctionalImpactReport",
]
