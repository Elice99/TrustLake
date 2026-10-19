"""
Profiling engine tests. Every expected value is computed independently of
pandas (by hand, or with Python's statistics module / plain counting), so
these genuinely check the profiler rather than echoing it back.
"""

import io
import json
import statistics
from collections.abc import Sequence

import pytest

from app.schemas.profile import ColumnProfile, DatasetProfile
from app.services.profiling import CsvParseError, profile_csv


def profile(data: str | bytes) -> DatasetProfile:
    raw = data.encode() if isinstance(data, str) else data
    return profile_csv(io.BytesIO(raw))


def col(p: DatasetProfile, name: str) -> ColumnProfile:
    return next(c for c in p.columns if c.name == name)


def one_column(values: Sequence[object]) -> str:
    return "v\n" + "\n".join(str(v) for v in values) + "\n"


def test_counts_missing_and_dtypes() -> None:
    p = profile("a,b,c\n1,x,\n2,,5\n3,y,6\n")
    assert (p.summary.row_count, p.summary.column_count) == (3, 3)
    assert p.summary.missing_cells == 2
    assert p.summary.missing_pct == pytest.approx(2 / 9 * 100)
    assert col(p, "b").missing_count == 1
    assert col(p, "b").missing_pct == pytest.approx(100 / 3)
    assert col(p, "a").dtype == "integer"
    assert col(p, "b").dtype == "string"
    # An integer column with a gap is read by pandas as float (documented).
    assert col(p, "c").dtype == "float"


def test_duplicate_rows_count_the_repeats_not_the_first() -> None:
    assert profile("a,b\n1,x\n1,x\n2,y\n1,x\n").summary.duplicate_rows == 2
    # Missing values compare equal when looking for duplicates.
    assert profile("a,b\n,x\n,x\n").summary.duplicate_rows == 1


def test_numeric_stats_and_iqr_outliers_match_python_statistics() -> None:
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]
    c = col(profile(one_column(values)), "v")
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr

    assert c.numeric_stats is not None and c.outliers is not None
    assert c.numeric_stats.min == 1 and c.numeric_stats.max == 100
    assert c.numeric_stats.mean == pytest.approx(statistics.mean(values))
    assert c.numeric_stats.median == pytest.approx(statistics.median(values))
    assert c.numeric_stats.std == pytest.approx(statistics.stdev(values))
    assert c.numeric_stats.q1 == pytest.approx(q1)
    assert c.numeric_stats.q3 == pytest.approx(q3)
    assert c.outliers.lower_bound == pytest.approx(lower)
    assert c.outliers.upper_bound == pytest.approx(upper)
    assert c.outliers.count == sum(1 for v in values if v < lower or v > upper) == 1


@pytest.mark.parametrize(
    ("values", "expected_id"),
    [
        ([i for i in range(25)], True),  # unique integers
        ([f"u{i}" for i in range(25)], True),  # unique text
        ([i for i in range(19)], False),  # too few rows to call it an ID
        ([i % 5 for i in range(25)], False),  # only 5 distinct values
        ([i + 0.5 for i in range(25)], False),  # unique floats are measurements
    ],
)
def test_potential_id_detection(values: list[object], expected_id: bool) -> None:
    assert col(profile(one_column(values)), "v").is_potential_id is expected_id


def test_constant_and_all_missing_columns() -> None:
    p = profile("k,m\nx,\nx,\nx,\n")
    assert col(p, "k").is_constant is True
    m = col(p, "m")
    assert m.is_constant is False
    assert m.missing_pct == 100
    assert m.uniqueness_ratio is None
    assert m.numeric_stats is None and m.outliers is None
    assert p.summary.constant_columns == 1


def test_mixed_type_flags_only_text_with_both_kinds() -> None:
    mixed = col(profile(one_column(["1", "2", "three", "4", "five"])), "v")
    assert mixed.dtype == "string"
    assert mixed.mixed_type is not None
    assert (mixed.mixed_type.numeric_count, mixed.mixed_type.non_numeric_count) == (
        3,
        2,
    )
    assert col(profile(one_column(["red", "blue", "red"])), "v").mixed_type is None


def test_booleans_get_no_numeric_statistics() -> None:
    c = col(profile(one_column(["True", "False", "True"])), "v")
    assert c.dtype == "boolean"
    assert c.numeric_stats is None and c.outliers is None


def test_profile_is_valid_json_even_with_nan_producing_cases() -> None:
    # A single value has no standard deviation (NaN), and an all-missing
    # column has no statistics at all: neither may leak NaN into JSON.
    p = profile("one,none\n5,\n")
    assert col(p, "one").numeric_stats is not None
    assert col(p, "one").numeric_stats.std is None  # type: ignore[union-attr]
    json.dumps(p.model_dump(mode="json"), allow_nan=False)


def test_kitchen_sink_matches_independent_counts() -> None:
    """The roadmap's cross-check: a messy file built row by row, with every
    expected number computed by plain Python, never by pandas."""
    rows: list[list[str]] = []
    for i in range(200):
        amount = 10_000 if i in (7, 77, 177) else 100 + (i % 50)  # 3 injected outliers
        rows.append(
            [
                "" if i % 10 == 0 else str(20 + i % 40),  # age, gaps
                "" if i % 25 == 0 else f"city{i % 4}",  # city, gaps
                (
                    f"ABC{i}" if i % 20 == 0 else str(i)
                ),  # code: numbers mixed with text, unique per row
                "same",  # constant
                str(amount),
            ]
        )
    rows += [list(r) for r in rows[:9]]  # 9 exact duplicate rows
    text = "age,city,code,flag,amount\n" + "\n".join(",".join(r) for r in rows) + "\n"
    p = profile(text)

    assert p.summary.row_count == len(rows) == 209
    assert p.summary.duplicate_rows == len(rows) - len({tuple(r) for r in rows}) == 9
    for idx, name in enumerate(["age", "city", "code", "flag", "amount"]):
        assert col(p, name).missing_count == sum(1 for r in rows if r[idx] == "")

    codes = [r[2] for r in rows]
    mixed = col(p, "code").mixed_type
    assert mixed is not None
    text_codes = sum(1 for c in codes if c.startswith("ABC"))
    assert mixed.non_numeric_count == text_codes
    assert mixed.numeric_count == len(codes) - text_codes

    amounts = [int(r[4]) for r in rows]
    q1, _, q3 = statistics.quantiles(amounts, n=4, method="inclusive")
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    outliers = col(p, "amount").outliers
    assert outliers is not None
    # 3 injected huge values + the duplicated copy of row 7, which is one of them.
    assert outliers.count == sum(1 for a in amounts if a < lo or a > hi) == 4
    assert col(p, "flag").is_constant is True


@pytest.mark.parametrize(
    ("data", "message_part"),
    [
        (b"", "empty"),
        (b"a,b\n", "no data rows"),
        (b"a,b\n1,2\n3,4,5\n", "not valid comma-separated"),
        (b"n\ncaf\xe9\n", "UTF-8"),
        (b"a,a\n1,2\n", "duplicate column names: a"),
    ],
)
def test_malformed_files_are_rejected_with_a_clear_message(
    data: bytes, message_part: str
) -> None:
    with pytest.raises(CsvParseError, match=message_part):
        profile(data)


def test_binary_garbage_is_rejected() -> None:
    with pytest.raises(CsvParseError):
        profile(bytes(range(256)) * 3)


def test_bom_is_tolerated_and_short_rows_pad_with_missing() -> None:
    assert [c.name for c in profile(b"\xef\xbb\xbfid,name\n1,x\n").columns] == [
        "id",
        "name",
    ]
    assert col(profile(b"a,b,c\n1,2\n"), "c").missing_count == 1
