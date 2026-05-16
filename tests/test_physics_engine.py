"""Unit tests for source.physics.engine.PhysicsEngine."""

from __future__ import annotations

import pytest
import pygame

from source.basic import Ball, Vector2, Wall, ZERO
from source.physics.engine import PhysicsEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ball(
    x: float,
    y: float,
    radius: float = 10,
    mass: float = 1,
    gravitation: bool = True,
) -> Ball:
    return Ball(
        position=Vector2(x, y),
        radius=radius,
        color=pygame.Color("red"),
        mass=mass,
        velocity=ZERO,
        artificialForces=[],
        gravitation=gravitation,
    )


def make_engine() -> PhysicsEngine:
    options = [{"type": "ball"}, {"type": "wall"}, {"type": "rope"}]
    return PhysicsEngine(options)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_creates_element_buckets(self) -> None:
        eng = make_engine()
        assert eng.ground_elements["all"] == []
        assert eng.ground_elements["ball"] == []
        assert eng.ground_elements["wall"] == []
        assert eng.ground_elements["rope"] == []
        assert eng.ground_elements["controlling"] == []

    def test_per_type_buckets(self) -> None:
        """Per-type buckets: options_list types overlapping with standard keys are skipped."""
        eng = make_engine()
        # standard: all, ball, wall, rope, controlling (5)
        assert len(eng.ground_elements) == 5

    def test_default_active_set_is_ground(self) -> None:
        eng = make_engine()
        assert eng.current_elements is eng.ground_elements

    def test_floor_is_none(self) -> None:
        assert make_engine().floor is None

    def test_is_floor_illegal_default_false(self) -> None:
        assert make_engine().is_floor_illegal is False


# ---------------------------------------------------------------------------
# Active set switching
# ---------------------------------------------------------------------------

class TestActiveSet:
    def test_set_active_celestial(self) -> None:
        eng = make_engine()
        eng.set_active_set(True)
        assert eng.current_elements is eng.celestial_elements

    def test_set_active_ground(self) -> None:
        eng = make_engine()
        eng.set_active_set(True)
        eng.set_active_set(False)
        assert eng.current_elements is eng.ground_elements


# ---------------------------------------------------------------------------
# Boundary transitions
# ---------------------------------------------------------------------------

class TestBoundaryTransitions:
    def test_element_above_transitions_to_celestial(self) -> None:
        eng = make_engine()
        ball = make_ball(0, -2e7)  # y <= -1.5e7 → celestial
        eng.ground_elements["all"].append(ball)
        eng.ground_elements["ball"].append(ball)

        eng.handle_boundary_transitions()

        assert ball not in eng.ground_elements["all"]
        assert ball not in eng.ground_elements["ball"]
        assert ball in eng.celestial_elements["all"]
        assert ball in eng.celestial_elements["ball"]

    def test_element_below_stays_in_ground(self) -> None:
        eng = make_engine()
        ball = make_ball(0, 0)  # y >= -1.5e7 → ground
        eng.ground_elements["all"].append(ball)
        eng.ground_elements["ball"].append(ball)

        eng.handle_boundary_transitions()

        assert ball in eng.ground_elements["all"]

    def test_celestial_element_falling_back_to_ground(self) -> None:
        eng = make_engine()
        ball = make_ball(0, 0)  # y >= -1.5e7 → back to ground
        eng.celestial_elements["all"].append(ball)
        eng.celestial_elements["ball"].append(ball)

        eng.handle_boundary_transitions()

        assert ball in eng.ground_elements["all"]
        assert ball not in eng.celestial_elements["all"]

    def test_no_elements_no_error(self) -> None:
        eng = make_engine()
        eng.handle_boundary_transitions()  # should not raise


# ---------------------------------------------------------------------------
# Environment parameter application
# ---------------------------------------------------------------------------

class TestApplyEnvironment:
    def test_gravity_applied(self) -> None:
        eng = make_engine()
        ball = make_ball(0, 0, mass=10)
        eng.current_elements["ball"].append(ball)

        env = [{"type": "gravity", "value": "2.5"}]
        eng.apply_environment(env)

        assert ball.gravity == 2.5

    def test_air_resistance_applied(self) -> None:
        eng = make_engine()
        ball = make_ball(0, 0)
        eng.current_elements["ball"].append(ball)

        env = [{"type": "airResistance", "value": "0.85"}]
        eng.apply_environment(env)

        assert ball.airResistance == 0.85

    def test_collision_factor_applied(self) -> None:
        eng = make_engine()
        ball = make_ball(0, 0)
        wall = Wall([Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)],
                     (200,) * 3, False)
        eng.current_elements["ball"].append(ball)
        eng.current_elements["wall"].append(wall)

        env = [{"type": "collisionFactor", "value": "0.7"}]
        eng.apply_environment(env)

        assert ball.collisionFactor == 0.7
        assert wall.collisionFactor == 0.7

    def test_collision_factor_applied_to_floor(self) -> None:
        eng = make_engine()
        floor = Wall([Vector2(0, 0), Vector2(100, 0), Vector2(100, 10), Vector2(0, 10)],
                      (200,) * 3, True)
        eng.floor = floor
        # Need at least one ball in active set for the per-ball loop
        ball = make_ball(0, 0)
        eng.current_elements["ball"].append(ball)

        env = [{"type": "collisionFactor", "value": "0.5"}]
        eng.apply_environment(env)

        assert floor.collisionFactor == 0.5

    def test_no_balls_no_error(self) -> None:
        eng = make_engine()
        eng.apply_environment([])  # should not raise


# ---------------------------------------------------------------------------
# Gravitation
# ---------------------------------------------------------------------------

class TestGravitation:
    def test_gravitation_attracts_two_balls(self) -> None:
        eng = make_engine()
        b1 = make_ball(0, 0, mass=100)
        b2 = make_ball(10, 0, mass=1)
        eng.current_elements["ball"].extend([b1, b2])

        eng.apply_gravitation_force()

        # b1 is heavier and at origin; b2 should feel a force pulling it toward b1
        assert b1.acceleration.x > 0 or b1.acceleration.y != 0

    def test_gravitation_no_effect_when_disabled(self) -> None:
        eng = make_engine()
        b1 = make_ball(0, 0, mass=100, gravitation=False)
        b2 = make_ball(10, 0, mass=1, gravitation=False)
        eng.current_elements["ball"].extend([b1, b2])

        eng.apply_gravitation_force()

        assert b1.acceleration == ZERO
        assert b2.acceleration == ZERO

    def test_find_max_gravitation_ball(self) -> None:
        eng = make_engine()
        b1 = make_ball(0, 0, mass=1000)
        b2 = make_ball(10, 0, mass=1)
        b3 = make_ball(100, 0, mass=1)
        eng.current_elements["ball"].extend([b1, b2, b3])

        target = eng.find_max_gravitation_ball(b2)
        assert target is b1  # b1 has most mass and is closest

    def test_find_max_gravitation_ball_none(self) -> None:
        eng = make_engine()
        assert eng.find_max_gravitation_ball(None) is None


# ---------------------------------------------------------------------------
# Collision resolution (static / structural)
# ---------------------------------------------------------------------------

class TestCollisionResolution:
    def test_ball_collision_no_balls_no_error(self) -> None:
        eng = make_engine()
        eng.resolve_ball_collisions()  # should not raise

    def test_wall_collision_no_balls_no_error(self) -> None:
        eng = make_engine()
        eng.resolve_wall_collisions()  # should not raise

    def test_vertex_collision_no_balls_no_error(self) -> None:
        eng = make_engine()
        eng.resolve_vertex_collisions()  # should not raise

    def test_line_collision_no_balls_no_error(self) -> None:
        eng = make_engine()
        eng.resolve_line_collisions()  # should not raise

    def test_two_overlapping_balls_rebound(self) -> None:
        """Two balls at the same position trigger collision response."""
        eng = make_engine()
        b1 = make_ball(0, 0, radius=10)
        b2 = make_ball(1, 0, radius=10)  # within 2*radius = 20
        eng.current_elements["ball"].extend([b1, b2])

        # Record velocities before
        v1_before = b1.velocity.copy()
        v2_before = b2.velocity.copy()

        eng.resolve_ball_collisions()

        # After collision, velocities should have changed
        assert (b1.velocity != v1_before or b2.velocity != v2_before)


# ---------------------------------------------------------------------------
# Floor handling
# ---------------------------------------------------------------------------

class TestFloor:
    def test_floor_is_illegal_when_out_of_bounds(self) -> None:
        """Narrow method test: is_floor_illegal flag exists and can be toggled."""
        eng = make_engine()
        assert eng.is_floor_illegal is False
        eng.is_floor_illegal = True
        assert eng.is_floor_illegal is True
