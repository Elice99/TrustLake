"""
Deterministic dataset profiling (PRD section 9, roadmap Stage 3).

No database, no FastAPI, no AI: a pure function from CSV bytes to a
DatasetProfile. Same file in, same profile out. Every metric has one
exact definition below, so each number can be re-derived by hand with
pandas, which is how the Stage 3 verification gate checks it.

DEFINITIONS (profiler_version 1)
  missing        pandas' default NA tokens (empty cell, NA, N/A, null,
                 NaN, ...). missing_pct = missing / rows * 100.
  duplicate row  identical to an EARLIER row in every column (missing
                 values compare equal). Counts the repeats, not the
                 first occurrence: pandas DataFrame.duplicated().sum().
  dtype          what pandas infers (low_memory=False so the whole
                 column is inferred at once). Known pandas behavior: an
                 integer column containing any missing value is read as
                 float. Reported faithfully, not "fixed", at this stage.
  unique_count   distinct non-missing values.
  constant       at least one non-missing value and exactly one distinct.
  potential ID   integer or text column, at least ID_MIN_NON_NULL
                 non-missing values, and uniqueness_ratio >=
                 ID_UNIQUENESS_THRESHOLD. Floats are excluded because
                 continuous measurements are naturally near-unique.
  outlier        IQR rule on numeric columns, see OutlierInfo.
  mixed type     text column where some non-missing values parse as
                 numbers and some do not (pandas.to_numeric).

INPUT LIMITS (v1): UTF-8 (a BOM is tolerated), comma-separated. Rows
with too many fields are rejected. Rows with too few fields are padded
with missing values, which is standard CSV behavior.
"""

import math
from typing import Any, BinaryIO

import pandas as pd

from app.schemas.profile import (
    ColumnProfile,
    DatasetProfile,
    DtypeLabel,
    MixedTypeInfo,
    NumericStats,
    OutlierInfo,
    ProfileSummary,
)

# Bump when any definition above changes, so stored profiles computed
# under older logic are never silently mixed with newer ones.
PROFILER_VERSION = 1

IQR_MULTIPLIER = 1.5
ID_UNIQUENESS_THRESHOLD = 0.99
ID_MIN_NON_NULL = 20


class CsvParseError(Exception):
    """The file is not a usable CSV. The message is written for the
    person who uploaded it, so it can be shown as-is."""


def read_csv_strict(fileobj: BinaryIO) -> pd.DataFrame:
    """Parses strictly and fails loudly. A silent partial parse would
    hand the user a profile of data that isn't what they uploaded."""
    try:
        # Read the raw header row first. pandas silently renames
        # duplicate headers (a, a -> a, a.1), which would hide a real
        # problem in the user's file.
        fileobj.seek(0)
        raw_header = pd.read_csv(
            fileobj,
            header=None,
            nrows=1,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        names = [str(v) for v in raw_header.iloc[0].tolist()]
        duplicates = sorted({n for n in names if n and names.count(n) > 1})
        if duplicates:
            raise CsvParseError(
                "The file has duplicate column names: "
                + ", ".join(duplicates)
                + ". Rename them so each column name is unique and upload again."
            )

        fileobj.seek(0)
        df = pd.read_csv(fileobj, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError as exc:
        raise CsvParseError(
            "The file is not valid UTF-8 text. In Excel, use Save As and "
            "choose 'CSV UTF-8', then upload again."
        ) from exc
    except pd.errors.EmptyDataError as exc:
        raise CsvParseError("The file is empty: no header row was found.") from exc
    except pd.errors.ParserError as exc:
        raise CsvParseError(
            f"The file is not valid comma-separated data. {str(exc).strip()}"
        ) from exc

    if len(df) == 0:
        raise CsvParseError("The file has a header row but no data rows.")
    return df


def _finite(value: Any) -> float | None:
    """NaN and infinity are not valid JSON (and Postgres JSONB rejects
    them), so every float that leaves this module goes through here."""
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    return as_float if math.isfinite(as_float) else None


def _dtype_label(series: pd.Series) -> DtypeLabel:
    # Boolean must be checked first: pandas counts bool as "numeric" in
    # some APIs, and we never want booleans to get numeric statistics.
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    # pandas 3 reads text as its own "str" dtype; older pandas used
    # "object". Accept both.
    if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
        return "string"
    return "other"


def _numeric_profile(
    series: pd.Series,
) -> tuple[NumericStats | None, OutlierInfo | None]:
    values = series.dropna().astype("float64")
    if values.empty:
        return None, None

    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - IQR_MULTIPLIER * iqr
    upper = q3 + IQR_MULTIPLIER * iqr

    stats = NumericStats(
        min=_finite(values.min()),
        max=_finite(values.max()),
        mean=_finite(values.mean()),
        median=_finite(values.median()),
        std=_finite(values.std()),  # ddof=1; NaN (-> None) for a single value
        q1=_finite(q1),
        q3=_finite(q3),
    )
    outliers = OutlierInfo(
        lower_bound=_finite(lower),
        upper_bound=_finite(upper),
        count=int(((values < lower) | (values > upper)).sum()),
    )
    return stats, outliers


def _mixed_type(series: pd.Series) -> MixedTypeInfo | None:
    present = series.dropna()
    if present.empty:
        return None
    numeric_count = int(pd.to_numeric(present, errors="coerce").notna().sum())
    non_numeric_count = len(present) - numeric_count
    if numeric_count > 0 and non_numeric_count > 0:
        return MixedTypeInfo(
            numeric_count=numeric_count, non_numeric_count=non_numeric_count
        )
    return None


def _profile_column(name: str, series: pd.Series, row_count: int) -> ColumnProfile:
    dtype = _dtype_label(series)
    missing_count = int(series.isna().sum())
    non_null = row_count - missing_count
    unique_count = int(series.nunique(dropna=True))
    ratio = (unique_count / non_null) if non_null > 0 else None

    is_potential_id = (
        dtype in ("integer", "string")
        and non_null >= ID_MIN_NON_NULL
        and ratio is not None
        and ratio >= ID_UNIQUENESS_THRESHOLD
    )

    stats: NumericStats | None = None
    outliers: OutlierInfo | None = None
    if dtype in ("integer", "float"):
        stats, outliers = _numeric_profile(series)

    return ColumnProfile(
        name=name,
        dtype=dtype,
        missing_count=missing_count,
        missing_pct=missing_count / row_count * 100,
        unique_count=unique_count,
        uniqueness_ratio=_finite(ratio),
        is_constant=non_null > 0 and unique_count == 1,
        is_potential_id=is_potential_id,
        numeric_stats=stats,
        outliers=outliers,
        mixed_type=_mixed_type(series) if dtype == "string" else None,
    )


def profile_dataframe(df: pd.DataFrame) -> DatasetProfile:
    row_count, column_count = df.shape
    # iloc, not df[name]: robust even if two columns ever shared a name.
    columns = [
        _profile_column(str(name), df.iloc[:, i], row_count)
        for i, name in enumerate(df.columns)
    ]

    missing_cells = sum(c.missing_count for c in columns)
    total_cells = row_count * column_count

    return DatasetProfile(
        profiler_version=PROFILER_VERSION,
        summary=ProfileSummary(
            row_count=row_count,
            column_count=column_count,
            missing_cells=missing_cells,
            missing_pct=missing_cells / total_cells * 100,
            duplicate_rows=int(df.duplicated().sum()),
            potential_outlier_values=sum(
                c.outliers.count for c in columns if c.outliers
            ),
            type_issue_columns=sum(1 for c in columns if c.mixed_type),
            constant_columns=sum(1 for c in columns if c.is_constant),
            potential_id_columns=sum(1 for c in columns if c.is_potential_id),
        ),
        columns=columns,
    )


def profile_csv(fileobj: BinaryIO) -> DatasetProfile:
    return profile_dataframe(read_csv_strict(fileobj))
