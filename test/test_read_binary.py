#!/usr/bin/env python3
from io import BytesIO
from typing import BinaryIO

import numpy as np
import pandas as pd
import pytest

from glue_analysis.readers.read_binary import (
    HEADER_NAMES,
    ParsingError,
    _read_correlators_binary,
)


@pytest.fixture()
def filename() -> str:
    return "testname.txt"


@pytest.fixture()
def header() -> dict[str, int]:
    return {name: i + 1 for i, name in enumerate(HEADER_NAMES)}


def create_corr_file(header: dict[str, int]) -> BytesIO:
    memory_file = BytesIO()
    memory_file.write(
        np.array([header[name] for name in HEADER_NAMES], dtype=np.float64).tobytes()
    )
    memory_file.seek(0)
    return memory_file


@pytest.fixture()
def corr_file(header: dict[str, int]) -> BytesIO:
    return create_corr_file(header)


@pytest.fixture()
def trivial_vevs() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Bin_index": np.arange(10, dtype=np.float64),
            "Operator_index": np.ones(10, dtype=np.float64),
            "Blocking_index": np.ones(10, dtype=np.float64),
            "Vac_exp": np.ones(10, dtype=np.float64),
        }
    )


def create_vev_file(vevs: pd.DataFrame) -> BytesIO:
    memory_file = BytesIO()
    memory_file.write(
        np.array([1 for name in HEADER_NAMES], dtype=np.float64).tobytes()
    )
    memory_file.write(np.asarray(vevs["Vac_exp"].values, dtype=np.float64).tobytes())
    memory_file.seek(0)
    return memory_file


### Trivial behavior


def test_read_correlators_binary_records_filename(
    corr_file: BinaryIO, filename: str
) -> None:
    answer = _read_correlators_binary(corr_file, filename)
    assert answer.filename == filename


def test_read_correlators_binary_does_not_create_vev_if_not_given(
    corr_file: BinaryIO, filename: str
) -> None:
    answer = _read_correlators_binary(corr_file, filename)
    assert "vevs" not in dir(answer)


def test_read_correlators_binary_freezes_the_ensemble(
    corr_file: BinaryIO, filename: str
) -> None:
    answer = _read_correlators_binary(corr_file, filename)
    assert answer._frozen


### Actually functional behavior

#### Metadata


def test_read_correlators_binary_makes_metadata_from_header_constant(
    filename: str,
) -> None:
    header = {name: 1 for name in HEADER_NAMES}
    corr_file = create_corr_file(header)
    answer = _read_correlators_binary(corr_file, filename)
    assert answer.metadata == header


def test_read_correlators_binary_makes_metadata_from_header_rising(
    filename: str,
) -> None:
    header = {name: i for i, name in enumerate(HEADER_NAMES)}
    corr_file = create_corr_file(header)
    answer = _read_correlators_binary(corr_file, filename)
    assert answer.metadata == header


def test_read_correlators_binary_merges_header_with_metadata(
    corr_file: BinaryIO, filename: str, header: dict[str, int]
) -> None:
    metadata = {"some": "metadata"}
    answer = _read_correlators_binary(corr_file, filename, metadata=metadata)
    assert answer.metadata == header | metadata


def test_read_correlators_binary_raises_on_conflicting_metadata(
    corr_file: BinaryIO, filename: str
) -> None:
    metadata = {HEADER_NAMES[0]: "conflict with header info"}
    with pytest.raises(ParsingError):
        _read_correlators_binary(corr_file, filename, metadata=metadata)


def test_read_correlators_binary_raises_on_any_doubly_specified_metadata(
    corr_file: BinaryIO, filename: str, header: dict[str, int]
) -> None:
    metadata = {
        HEADER_NAMES[0]: header[HEADER_NAMES[0]]  # same as header but still forbidden
    }
    with pytest.raises(ParsingError):
        _read_correlators_binary(corr_file, filename, metadata=metadata)


#### VEVs


def test_read_correlators_binary_reads_trivial_vev(
    corr_file: BinaryIO, filename: str, trivial_vevs: pd.DataFrame
) -> None:
    answer = _read_correlators_binary(
        corr_file, filename, vev_file=create_vev_file(trivial_vevs)
    )
    assert (answer.vevs == trivial_vevs).all().all()


def test_read_correlators_binary_reads_linear_vevs(
    corr_file: BinaryIO, filename: str, trivial_vevs: pd.DataFrame
) -> None:
    trivial_vevs["Vac_exp"] = range(trivial_vevs.shape[0])
    answer = _read_correlators_binary(
        corr_file, filename, vev_file=create_vev_file(trivial_vevs)
    )
    assert (answer.vevs == trivial_vevs).all().all()
