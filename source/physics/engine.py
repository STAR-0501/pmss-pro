"""Physics engine for PMSS-Pro.

Encapsulates physical state (element collections) and pure physics
computation, separated from the ``Game`` class to reduce the God-class
problem and enable unit-testing of physics logic in isolation.
"""

from __future__ import annotations

from typing import Any

from ..basic import Ball, Wall, gravityFactor


# ---------------------------------------------------------------------------
# PhysicsEngine
# ---------------------------------------------------------------------------

class PhysicsEngine:
    """Owns physical element collections and runs inter-element physics.

    Responsibilities
    ----------------
    * Maintaining ``elements``, ``groundElements``, ``celestialElements``.
    * Boundary transitions (ground ↔ celestial).
    * Ball--ball, ball--wall and ball--floor collision detection & response.
    * Gravitational force calculation.
    * Environment parameter application (gravity, air resistance, ...).

    The engine deliberately does **not** handle rendering or UI input,
    making it testable in isolation.
    """

    def __init__(self, options_list: list[dict[str, Any]]) -> None:
        # -- element collections -------------------------------------------

        _base: dict[str, list] = {
            "all": [],
            "ball": [],
            "wall": [],
            "rope": [],
            "controlling": [],
        }

        self.ground_elements: dict[str, list] = {
            k: [] for k in _base
        }
        self.celestial_elements: dict[str, list] = {
            k: [] for k in _base
        }

        # Add per-type buckets from options list
        for opt in options_list:
            t: str = opt["type"]
            if t not in self.ground_elements:
                self.ground_elements[t] = []
            if t not in self.celestial_elements:
                self.celestial_elements[t] = []

        # Active set (reference, not a copy)
        self.current_elements: dict[str, list] = self.ground_elements

        # Floor (also a wall, positioned by Game)
        self.floor: Wall | None = None
        self.is_floor_illegal: bool = False

    # ------------------------------------------------------------------
    # Public helpers -- used by Game properties / methods
    # ------------------------------------------------------------------

    @property
    def elements(self) -> dict[str, list]:
        """Alias for the currently active element set."""
        return self.current_elements

    def set_active_set(self, use_celestial: bool) -> None:
        """Switch the active element set for ground/celestial mode."""
        self.current_elements = (
            self.celestial_elements if use_celestial else self.ground_elements
        )

    # ------------------------------------------------------------------
    # Boundary transitions
    # ------------------------------------------------------------------

    def handle_boundary_transitions(self) -> None:
        """Move elements between ground/celestial sets based on y-position.

        ``position.y <= -1.5e7`` -> celestial;
        ``position.y >= -1.5e7`` -> ground.
        """
        for elem in list(self.ground_elements["all"]):
            if elem.position.y <= -1.5e7:
                self.ground_elements["all"].remove(elem)
                self.ground_elements[elem.type].remove(elem)
                self.celestial_elements["all"].append(elem)
                self.celestial_elements[elem.type].append(elem)

        for elem in list(self.celestial_elements["all"]):
            if elem.position.y >= -1.5e7:
                self.celestial_elements["all"].remove(elem)
                self.celestial_elements[elem.type].remove(elem)
                self.ground_elements["all"].append(elem)
                self.ground_elements[elem.type].append(elem)

    # ------------------------------------------------------------------
    # Environment parameter application
    # ------------------------------------------------------------------

    def apply_environment(self, environment_options: list[dict[str, Any]]) -> None:
        """Apply gravity, air resistance and collision factor to all balls."""
        for ball in self.current_elements["ball"]:
            for opt in environment_options:
                t = opt["type"]
                v = opt["value"]
                if t == "gravity":
                    ball.gravity = float(v)
                elif t == "airResistance":
                    ball.airResistance = float(v)
                elif t == "collisionFactor":
                    ball.collisionFactor = float(v)
                    for wall in self.current_elements["wall"]:
                        wall.collisionFactor = float(v)
                    if self.floor is not None:
                        self.floor.collisionFactor = float(v)

    # ------------------------------------------------------------------
    # Collision detection & response
    # ------------------------------------------------------------------

    def resolve_ball_collisions(self) -> None:
        """Detect and respond to ball-ball collisions."""
        balls: list[Ball] = self.current_elements["ball"]
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                if balls[i].isCollidedByBall(balls[j]):
                    balls[i].reboundByBall(balls[j])

    def resolve_wall_collisions(self) -> None:
        """Ball-wall and ball-floor collisions."""
        balls: list[Ball] = self.current_elements["ball"]
        for wall in self.current_elements["wall"]:
            for ball in balls:
                if wall.isPosOn(None, ball.position):
                    ball.reboundByWall(wall)

        if self.floor is not None:
            for ball in balls:
                for line in self.floor.lines:
                    if ball.isCollidedByLine(line):
                        ball.reboundByLine(line)
                if self.floor.isPosOn(None, ball.position):
                    ball.reboundByWall(self.floor)

    def resolve_vertex_collisions(self) -> None:
        """Check wall vertex collisions with balls."""
        for wall in self.current_elements["wall"]:
            for ball in self.current_elements["ball"]:
                wall.checkVertexCollision(ball)

    def resolve_line_collisions(self) -> None:
        """Check ball-wall line segment collisions."""
        for wall in self.current_elements["wall"]:
            for line in wall.lines:
                for ball in self.current_elements["ball"]:
                    if (
                        ball.isCollidedByLine(line)
                        and not wall.isPosOn(None, ball.position)
                    ):
                        ball.reboundByLine(line)

    # ------------------------------------------------------------------
    # Gravitation
    # ------------------------------------------------------------------

    def apply_gravitation_force(self) -> None:
        """Apply inter-body gravitational force for celestial-mode balls."""
        balls: list[Ball] = self.current_elements["ball"]
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                b1, b2 = balls[i], balls[j]
                if not (b1.gravitation or b2.gravitation):
                    continue
                dv = b2.position - b1.position
                dist = dv.magnitude()
                if dist < 1e-6:
                    continue
                f_mag = gravityFactor * b1.mass * b2.mass / (dist * dist)
                dir_vec = dv / dist
                b1.force(dir_vec * f_mag, isNatural=True)
                b2.force(-dir_vec * f_mag, isNatural=True)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def find_max_gravitation_ball(self, ball: Ball) -> Ball | None:
        """Return the ball exerting the strongest gravitational pull."""
        if ball is None:
            return None
        result: Ball | None = None
        max_g: float = 0.0
        for other in self.current_elements["ball"]:
            if other is ball:
                continue
            d = ball.position.distance(other.position)
            g = gravityFactor * ball.mass * other.mass / (d * d + 1e-6)
            if g > max_g:
                max_g = g
                result = other
        return result
