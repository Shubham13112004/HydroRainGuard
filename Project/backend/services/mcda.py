"""
Multi-criteria decision analysis (MCDA) using the Analytic Hierarchy
Process (AHP).

AHP is a published, peer-reviewed decision method (T.L. Saaty,
"The Analytic Hierarchy Process", McGraw-Hill, 1980). It is used here
instead of ad-hoc "+10 if rainfall is high" adjustments so that the
recommendation engine is:

  * auditable  -- every weight is derived from a stated pairwise
                  comparison matrix, and the matrix's internal
                  consistency is checked and reported;
  * defensible -- criteria are normalised to a common 0-1 scale before
                  being combined, so a score in mm is never added to a
                  score in m2.

The engine is deterministic and rule-based. It is NOT machine learning:
there is no training data, no model weights, and no learned parameters.
"""

import math

# ------------------------------------------------------------------
# 1. Criteria
# ------------------------------------------------------------------

CRITERIA = [
    "harvestable_yield",   # annual litres the catchment can deliver
    "annual_rainfall",     # mm/yr at the site
    "soil_infiltration",   # mm/hr -- governs whether recharge works
    "open_space",          # m2 available for the structure
    "groundwater_depth",   # m below ground level
]

# ------------------------------------------------------------------
# 2. Pairwise comparison matrix (Saaty 1-9 scale)
# ------------------------------------------------------------------
#
# a[i][j] means "criterion i is a[i][j] times as important as
# criterion j for choosing a rainwater harvesting structure".
# The matrix is reciprocal by construction: a[j][i] = 1 / a[i][j].
#
# Rationale, in the order the criteria are listed above:
#
#   yield > rainfall (2)      Rainfall is the driver, but the volume a
#                             roof actually delivers is what determines
#                             whether a structure is worth building.
#   yield > infiltration (3)  A site with plenty of water but poor soil
#                             can still use storage; a site with no
#                             water cannot use anything.
#   yield > open space (4)    Volume is the harder constraint: you can
#                             find space, you cannot invent rainfall.
#   yield > depth (5)         Depth matters only for recharge structures.
#   rainfall > infiltration (2)
#   rainfall > open space (3)
#   rainfall > depth (4)
#   infiltration > open space (2)
#   infiltration > depth (3)  Soil decides whether *recharge* is viable
#                             at all; depth only sizes it.
#   open space > depth (2)
#
# These judgements are engineering priors, stated openly so a reviewer
# can substitute their own matrix. The consistency test below confirms
# the set is not self-contradictory.

_TRI = {
    ("harvestable_yield", "annual_rainfall"): 2,
    ("harvestable_yield", "soil_infiltration"): 3,
    ("harvestable_yield", "open_space"): 4,
    ("harvestable_yield", "groundwater_depth"): 5,
    ("annual_rainfall", "soil_infiltration"): 2,
    ("annual_rainfall", "open_space"): 3,
    ("annual_rainfall", "groundwater_depth"): 4,
    ("soil_infiltration", "open_space"): 2,
    ("soil_infiltration", "groundwater_depth"): 3,
    ("open_space", "groundwater_depth"): 2,
}

# Saaty's random consistency index for n = 1..10. A perfectly
# consistent matrix has RI = 0; these are the mean CI of randomly
# generated reciprocal matrices of each order.
_RANDOM_INDEX = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
}


def build_pairwise_matrix() -> list[list[float]]:
    n = len(CRITERIA)
    m = [[1.0] * n for _ in range(n)]
    for i, a in enumerate(CRITERIA):
        for j, b in enumerate(CRITERIA):
            if i == j:
                m[i][j] = 1.0
            elif (a, b) in _TRI:
                m[i][j] = float(_TRI[(a, b)])
            elif (b, a) in _TRI:
                m[i][j] = 1.0 / float(_TRI[(b, a)])
            else:  # pragma: no cover - CRITERIA is fully connected
                m[i][j] = 1.0
    return m


def ahp_weights(matrix: list[list[float]]) -> dict:
    """
    Derive criterion weights from a reciprocal pairwise matrix using
    the geometric-mean (power) method, and check consistency.

    Returns weights, lambda_max, CI, CR and whether CR <= 0.10
    (Saaty's acceptability threshold).
    """
    n = len(matrix)

    # Geometric mean of each row.
    gm = [math.prod(row) ** (1.0 / n) for row in matrix]
    total = sum(gm)
    weights = [g / total for g in gm]

    # Principal eigenvalue: mean of (A w)_i / w_i.
    lam_sum = 0.0
    for i in range(n):
        aw = sum(matrix[i][j] * weights[j] for j in range(n))
        lam_sum += aw / weights[i] if weights[i] else 0.0
    lambda_max = lam_sum / n

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = _RANDOM_INDEX.get(n, 1.49)
    cr = (ci / ri) if ri else 0.0

    return {
        "weights": {c: w for c, w in zip(CRITERIA, weights)},
        "lambda_max": round(lambda_max, 4),
        "consistency_index": round(ci, 4),
        "consistency_ratio": round(cr, 4),
        "consistent": cr <= 0.10,
    }


# ------------------------------------------------------------------
# 3. Value / utility functions
# ------------------------------------------------------------------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def ramp(value: float, low: float, high: float) -> float:
    """0 at or below `low`, 1 at or above `high`, linear between."""
    if high <= low:
        return 1.0 if value >= high else 0.0
    return clamp01((value - low) / (high - low))


def trapezoid(
    value: float,
    a: float, b: float, c: float, d: float,
) -> float:
    """
    Standard MCDA trapezoidal utility: 0 below a, rising 0->1 over
    [a,b], flat 1 on [b,c], falling 1->0 over [c,d], 0 above d.
    """
    if b <= a:  # no rising limb -> step up at a
        left = 1.0 if value >= a else 0.0
    else:
        left = clamp01((value - a) / (b - a))
    if d <= c:  # no falling limb -> step down at c
        right = 1.0 if value <= c else 0.0
    else:
        right = clamp01((d - value) / (d - c))
    return min(left, right)
