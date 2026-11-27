from math import log2

import pytest

from app.evaluate import dcg, metrics


def test_dcg_uses_linear_gain_and_rank_discount():
    assert dcg([3, 2, 1], 2) == pytest.approx(3 + 2 / log2(3))


def test_metrics_use_full_eligible_pool_and_fixed_k():
    p5, r5, n5, p10, r10, n10 = metrics(["a", "c"], {"a": 3, "b": 2, "c": 0})
    assert (p5, r5, p10, r10) == (0.2, 0.5, 0.1, 0.5)
    assert n5 == n10 == pytest.approx(3 / (3 + 2 / log2(3)))


def test_metrics_handle_zero_denominators_and_weak_grades():
    assert metrics([], {}).tolist() == [0] * 6
    assert metrics(["a"], {"a": 0}).tolist() == [0] * 6
    assert metrics(["a"], {"a": 1}).tolist() == [0, 0, 1, 0, 0, 1]
