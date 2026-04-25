"""
Pydantic schemas for the calculation statistics feature.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OperationStat(BaseModel):
    """Usage breakdown for a single operation type."""
    type: str = Field(..., description="Calculation type (e.g. 'addition')")
    count: int = Field(..., ge=0, description="Number of times this type was used")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Share of total calculations (%)")

    model_config = ConfigDict(from_attributes=True)


class StatsResponse(BaseModel):
    """
    Full statistics payload returned by GET /stats.
    All metrics are scoped to the authenticated user.
    """
    # Totals
    total_calculations: int = Field(..., ge=0, description="Total calculations performed")
    total_operands: int = Field(..., ge=0, description="Sum of all input lengths across every calculation")

    # Averages
    avg_operands_per_calculation: float = Field(
        ..., ge=0.0,
        description="Mean number of operands per calculation"
    )
    avg_result: Optional[float] = Field(
        None,
        description="Mean numeric result across all calculations (None when no calculations)"
    )
    max_result: Optional[float] = Field(None, description="Largest result value")
    min_result: Optional[float] = Field(None, description="Smallest result value")

    # Breakdowns
    operations_breakdown: List[OperationStat] = Field(
        default_factory=list,
        description="Per-type counts and percentages, sorted by count desc"
    )
    most_used_operation: Optional[str] = Field(
        None, description="Operation type used most frequently"
    )
    least_used_operation: Optional[str] = Field(
        None, description="Operation type used least frequently"
    )

    # Activity
    last_calculation_at: Optional[datetime] = Field(
        None, description="Timestamp of the most recent calculation"
    )
    first_calculation_at: Optional[datetime] = Field(
        None, description="Timestamp of the first calculation"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "total_calculations": 10,
                "total_operands": 25,
                "avg_operands_per_calculation": 2.5,
                "avg_result": 42.0,
                "max_result": 100.0,
                "min_result": 1.0,
                "operations_breakdown": [
                    {"type": "addition", "count": 6, "percentage": 60.0},
                    {"type": "division", "count": 4, "percentage": 40.0},
                ],
                "most_used_operation": "addition",
                "least_used_operation": "division",
                "last_calculation_at": "2025-01-10T12:00:00",
                "first_calculation_at": "2025-01-01T09:00:00",
            }
        }
    )
