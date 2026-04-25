"""
Business logic for computing per-user calculation statistics.

Kept as a pure service layer (no FastAPI dependencies) so it can be unit-tested
without an HTTP client or a running server.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.calculation import Calculation
from app.schemas.stats import OperationStat, StatsResponse


def compute_stats(user_id, db: Session) -> StatsResponse:
    """
    Compute usage statistics for *user_id* from the database.

    All queries are scoped to the given user; no cross-user data is exposed.
    Returns a fully-populated StatsResponse even when the user has no calculations.
    """
    base_q = db.query(Calculation).filter(Calculation.user_id == user_id)
    calculations: List[Calculation] = base_q.all()

    total = len(calculations)

    if total == 0:
        return StatsResponse(
            total_calculations=0,
            total_operands=0,
            avg_operands_per_calculation=0.0,
            avg_result=None,
            max_result=None,
            min_result=None,
            operations_breakdown=[],
            most_used_operation=None,
            least_used_operation=None,
            last_calculation_at=None,
            first_calculation_at=None,
        )

    # operands
    total_operands: int = sum(
        len(c.inputs) if isinstance(c.inputs, list) else 0
        for c in calculations
    )
    avg_operands: float = round(total_operands / total, 4)

    # results
    results = [c.result for c in calculations if c.result is not None]
    avg_result: Optional[float] = round(sum(results) / len(results), 4) if results else None
    max_result: Optional[float] = max(results) if results else None
    min_result: Optional[float] = min(results) if results else None

    # per-type counts
    type_counts: dict = {}
    for c in calculations:
        type_counts[c.type] = type_counts.get(c.type, 0) + 1

    breakdown = sorted(
        [
            OperationStat(
                type=op_type,
                count=count,
                percentage=round(count / total * 100, 2),
            )
            for op_type, count in type_counts.items()
        ],
        key=lambda s: (-s.count, s.type),
    )

    most_used: Optional[str]  = breakdown[0].type  if breakdown else None
    least_used: Optional[str] = breakdown[-1].type if breakdown else None

    # activity timestamps
    timestamps = [c.created_at for c in calculations if c.created_at is not None]
    last_at  = max(timestamps) if timestamps else None
    first_at = min(timestamps) if timestamps else None

    return StatsResponse(
        total_calculations=total,
        total_operands=total_operands,
        avg_operands_per_calculation=avg_operands,
        avg_result=avg_result,
        max_result=max_result,
        min_result=min_result,
        operations_breakdown=breakdown,
        most_used_operation=most_used,
        least_used_operation=least_used,
        last_calculation_at=last_at,
        first_calculation_at=first_at,
    )
