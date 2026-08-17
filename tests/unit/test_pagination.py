from __future__ import annotations

from nqct.httpss.pagination import PageIterator


def test_page_iterator_from_list() -> None:
    items = PageIterator([1, 2, 3])
    assert list(items) == [1, 2, 3]


def test_page_iterator_from_payload() -> None:
    page = PageIterator.from_payload({"items": ["a", "b"], "total": 2})
    assert list(page) == ["a", "b"]

    empty = PageIterator.from_payload({"unexpected": True})
    assert list(empty) == []
