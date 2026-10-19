"""
Dataset profile schemas (PRD section 9).

A profile is *evidence* about a dataset, never a verdict: counts,
percentages and flags computed deterministically from the data. Every
field is defined exactly in app/services/profiling.py so any number here
can be re-derived by hand with pandas.
"""

from typing import Literal

from pydantic import BaseModel

# "integer"/"float"/"boolean" mirror what pandas infers when reading the
# CSV. "string" is any text column. "other" is a safety net so an
# unexpected pandas dtype can never crash profiling.
DtypeLabel = Literal["integer", "float", "boolean", "string", "other"]


class NumericStats(BaseModel):
    min: float | None
    max: float | None
    mean: float | None
    median: float | None
    std: float | None  # sample standard deviation (ddof=1); None when < 2 values
    q1: float | None  # 25th percentile, linear interpolation (pandas default)
    q3: float | None  # 75th percentile, linear interpolation (pandas default)


class OutlierInfo(BaseModel):
    """IQR rule: a value is an outlier when it is below q1 - 1.5*IQR or
    above q3 + 1.5*IQR. Evidence only, nothing is removed or changed."""

    lower_bound: float | None
    upper_bound: float | None
    count: int


class MixedTypeInfo(BaseModel):
    """Present only on text columns where some non-missing values parse
    as numbers and others do not (both counts above zero)."""

    numeric_count: int
    non_numeric_count: int


class ColumnProfile(BaseModel):
    name: str
    dtype: DtypeLabel
    missing_count: int
    missing_pct: float  # percent of this column's rows, 0-100, unrounded
    unique_count: int  # distinct non-missing values
    uniqueness_ratio: float | None  # unique_count / non-missing count
    is_constant: bool
    is_potential_id: bool
    numeric_stats: NumericStats | None = None
    outliers: OutlierInfo | None = None
    mixed_type: MixedTypeInfo | None = None


class ProfileSummary(BaseModel):
    row_count: int
    column_count: int
    missing_cells: int
    missing_pct: float  # percent of all cells, 0-100, unrounded
    duplicate_rows: int
    potential_outlier_values: int  # sum of per-column outlier counts
    type_issue_columns: int  # columns flagged mixed_type
    constant_columns: int
    potential_id_columns: int


class DatasetProfile(BaseModel):
    profiler_version: int
    summary: ProfileSummary
    columns: list[ColumnProfile]
