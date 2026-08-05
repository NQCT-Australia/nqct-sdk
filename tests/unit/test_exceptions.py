from __future__ import annotations

import pytest
from nqct.exceptions import (
    AuthenticationError,
    JobFailedError,
    JobNotCompleteError,
    JobTimeoutError,
    NQCTError,
)


def test_exception_hierarchy() -> None:
    err = AuthenticationError("bad key", status_code=401, detail="nope")
    assert isinstance(err, NQCTError)
    assert err.status_code == 401
    assert err.detail == "nope"
    assert str(err) == "bad key"


@pytest.mark.parametrize(
    "exc_type",
    [JobFailedError, JobNotCompleteError, JobTimeoutError],
)
def test_job_exceptions(exc_type: type[NQCTError]) -> None:
    assert issubclass(exc_type, NQCTError)
