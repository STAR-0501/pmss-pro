"""Unit tests for source.basic.vector2.Vector2."""

from __future__ import annotations

import math
import pytest
from source.basic.vector2 import Vector2


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_from_xy(self) -> None:
        v = Vector2(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_from_int_xy(self) -> None:
        v = Vector2(3, 4)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_from_vector2(self) -> None:
        orig = Vector2(1.5, 2.5)
        v = Vector2(orig)
        assert v.x == 1.5
        assert v.y == 2.5
        assert v is not orig  # should be a copy

    def test_from_tuple(self) -> None:
        v = Vector2((10.0, 20.0))
        assert v.x == 10.0
        assert v.y == 20.0

    def test_from_int_tuple(self) -> None:
        v = Vector2((1, 2))
        assert v.x == 1.0
        assert v.y == 2.0

    def test_from_tuple_classmethod(self) -> None:
        v = Vector2.from_tuple((7.0, 8.0))
        assert v.x == 7.0
        assert v.y == 8.0


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

class TestArithmetic:
    def test_add(self) -> None:
        a = Vector2(1, 2)
        b = Vector2(3, 4)
        assert a + b == Vector2(4, 6)

    def test_sub(self) -> None:
        a = Vector2(5, 7)
        b = Vector2(2, 3)
        assert a - b == Vector2(3, 4)

    def test_mul(self) -> None:
        v = Vector2(2, 3)
        assert v * 3 == Vector2(6, 9)

    def test_rmul(self) -> None:
        v = Vector2(2, 3)
        assert 3 * v == Vector2(6, 9)

    def test_truediv(self) -> None:
        v = Vector2(6, 9)
        assert v / 3 == Vector2(2, 3)

    def test_neg(self) -> None:
        v = Vector2(1, -2)
        assert -v == Vector2(-1, 2)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

class TestComparison:
    def test_eq_equal(self) -> None:
        assert Vector2(3, 4) == Vector2(3, 4)

    def test_eq_not_equal(self) -> None:
        assert Vector2(3, 4) != Vector2(3, 5)

    def test_eq_not_vector(self) -> None:
        assert (Vector2(1, 2) == (1, 2)) is False

    def test_ne_not_vector(self) -> None:
        assert (Vector2(1, 2) != (1, 2)) is True


# ---------------------------------------------------------------------------
# Magnitude / normalization
# ---------------------------------------------------------------------------

class TestMagnitude:
    def test_magnitude_zero(self) -> None:
        assert Vector2(0, 0).magnitude() == 0.0

    def test_magnitude(self) -> None:
        assert Vector2(3, 4).magnitude() == pytest.approx(5.0)

    def test_magnitude_squared(self) -> None:
        assert Vector2(3, 4).magnitude_squared() == 25.0

    def test_abs(self) -> None:
        assert abs(Vector2(3, 4)) == pytest.approx(5.0)

    def test_normalized(self) -> None:
        v = Vector2(3, 4)
        n = v.normalized()
        assert abs(n) == pytest.approx(1.0)
        assert v == Vector2(3, 4)  # original unchanged

    def test_normalized_zero(self) -> None:
        assert Vector2(0, 0).normalized() == Vector2(0, 0)

    def test_normalize_mutates(self) -> None:
        v = Vector2(3, 4)
        result = v.normalize()
        assert abs(v) == pytest.approx(1.0)
        assert result is v  # returns self

    def test_normalize_zero(self) -> None:
        v = Vector2(0, 0)
        v.normalize()
        assert v == Vector2(0, 0)


# ---------------------------------------------------------------------------
# Dot / Cross / Distance
# ---------------------------------------------------------------------------

class TestDotCrossDistance:
    def test_dot(self) -> None:
        assert Vector2(1, 0).dot(Vector2(0, 1)) == 0.0
        assert Vector2(1, 0).dot(Vector2(1, 0)) == 1.0
        assert Vector2(1, 2).dot(Vector2(3, 4)) == 11.0

    def test_cross(self) -> None:
        assert Vector2(1, 0).cross(Vector2(0, 1)) == pytest.approx(1.0)
        assert Vector2(0, 1).cross(Vector2(1, 0)) == pytest.approx(-1.0)

    def test_distance(self) -> None:
        assert Vector2(0, 0).distance(Vector2(3, 4)) == pytest.approx(5.0)

    def test_distance_squared(self) -> None:
        assert Vector2(0, 0).distance_squared(Vector2(3, 4)) == 25.0


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

class TestProjection:
    def test_project_onto_axis(self) -> None:
        v = Vector2(3, 4)
        p = v.project(Vector2(1, 0))
        assert p == Vector2(3, 0)

    def test_project_onto_zero(self) -> None:
        assert Vector2(3, 4).project(Vector2(0, 0)) == Vector2(0, 0)

    def test_project_vertical(self) -> None:
        v = Vector2(3, 4)
        pv = v.projectVertical(Vector2(1, 0))
        assert pv == Vector2(0, 4)

    def test_vertical(self) -> None:
        assert Vector2(1, 2).vertical() == Vector2(-2, 1)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

class TestUtility:
    def test_copy(self) -> None:
        v = Vector2(1, 2)
        c = v.copy()
        assert c == v
        assert c is not v

    def test_to_tuple(self) -> None:
        assert Vector2(1.5, 2.5).toTuple() == (1.5, 2.5)

    def test_to_int_tuple(self) -> None:
        assert Vector2(1.5, 2.7).toIntTuple() == (1, 2)

    def test_lerp(self) -> None:
        a = Vector2(0, 0)
        b = Vector2(10, 20)
        mid = a.lerp(b, 0.5)
        assert mid == Vector2(5, 10)

    def test_lerp_t0(self) -> None:
        assert Vector2(0, 0).lerp(Vector2(10, 20), 0) == Vector2(0, 0)

    def test_lerp_t1(self) -> None:
        assert Vector2(0, 0).lerp(Vector2(10, 20), 1) == Vector2(10, 20)

    def test_zero_mutates(self) -> None:
        v = Vector2(3, 4)
        result = v.zero()
        assert v == Vector2(0, 0)
        assert result is v

    def test_getitem(self) -> None:
        v = Vector2(1.5, 2.5)
        assert v[0] == 1.5
        assert v[1] == 2.5

    def test_getitem_out_of_range(self) -> None:
        with pytest.raises(IndexError):
            _ = Vector2(1, 2)[2]

    def test_repr(self) -> None:
        v = Vector2(3.14159, 2.71828)
        r = repr(v)
        assert r.startswith("Vector2(")
        assert "3.1416" in r

    def test_from_angle(self) -> None:
        # 90 degrees → (0, 1)
        v = Vector2.from_angle(math.pi / 2)
        assert v.x == pytest.approx(0.0, abs=1e-10)
        assert v.y == pytest.approx(1.0, abs=1e-10)

        # 45 degrees → (√2/2, √2/2)
        v = Vector2.from_angle(math.pi / 4)
        assert v.x == pytest.approx(math.sqrt(2) / 2)
        assert v.y == pytest.approx(math.sqrt(2) / 2)
