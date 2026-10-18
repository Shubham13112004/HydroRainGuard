"""
Gridded rainfall climatology lookup.

This module is the project's GIS raster layer. It samples a real,
global, gridded precipitation climatology at an arbitrary coordinate
using bilinear interpolation between the four surrounding grid-cell
centres, and reports the provenance of whatever it returns.

DATA
----
NOAA PSL CMAP (CPC Merged Analysis of Precipitation), long-term monthly
means for 1991-2020, gridded at 2.5 degrees (72 lat x 144 lon).

    https://psl.noaa.gov/data/gridded/data.cmap.html

CMAP merges rain-gauge observations with five satellite estimates
(GPI, OPI, SSM/I scattering, SSM/I emission, AMSU), so it has genuine
global coverage including ocean and desert, where gauge-only products
are undefined. It is a US Government product and is in the public
domain. Build it with `scripts/build_rainfall_grid.py`.

WHY THIS REPLACED THE OLD LOOKUP TABLE
--------------------------------------
The previous implementation held ten hand-written lat/lon boxes for
Indian metros plus a catch-all that returned 1100 mm for *any* other
coordinate, with an Indian monsoon seasonal profile. Every location
outside India -- New York, London, Nairobi -- silently received an
Indian monsoon. This module has no such failure mode.

HONEST LIMITATION: RESOLUTION
-----------------------------
2.5 degrees is about 278 km. That resolves continents, not districts.
Where rainfall changes sharply over short distances the cell average
will be wrong for a specific site. The clearest case is Pune: the grid
cell containing Pune (centre 18.75N, 73.75E) also contains the Western
Ghats crest, where annual rainfall exceeds 4000 mm, so the cell mean
(~1400 mm) is roughly double Pune city's ~700 mm.

Two things are done about that rather than hiding it:

1. `sample()` reports the cell centre, resolution and source, so the
   UI and the PDF state exactly where the number came from.
2. `scale_to_annual()` lets a caller (or the user, via
   `annual_rainfall_override`) keep the grid's *seasonal shape* while
   substituting a locally-known annual total. Combining a coarse grid's
   monthly distribution with a local gauge total is standard practice
   and is far better than either input alone.

If a higher-resolution regional raster (IMD 0.25 degree, CHIRPS) is
available, drop it in via the same interface -- nothing else changes.
"""

from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass
from functools import lru_cache

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)
BIN_PATH = os.path.join(DATA_DIR, "precip_climatology.bin")
META_PATH = os.path.join(DATA_DIR, "precip_climatology.json")

N_LAT = 72
N_LON = 144
N_MONTHS = 12
CELL = 2.5

LAT_FIRST = 90.0 - CELL / 2      # 88.75, north edge, descending
LON_FIRST = CELL / 2             # 1.25, centre of the first cell

NO_DATA = 65535


@dataclass(frozen=True)
class RainfallSample:
    """Result of sampling the climatology at one point."""

    monthly_mm: list[float]          # 12 months
    annual_mm: float
    cell_lat: float                  # nearest cell centre
    cell_lon: float
    resolution_deg: float
    source: str
    period: str
    valid_years: int                 # years of data behind the mean
    interpolated: bool               # True when between cell centres
    scaled_to_override: bool = False

    def describe(self) -> str:
        """One-line provenance string for the UI and the report."""
        base = f"{self.source}, {self.resolution_deg:g}° grid"
        if self.scaled_to_override:
            return f"{base} (monthly distribution) + local annual total"
        return base


class _Grid:
    """Parsed raster: month-major, then row (N->S), then column."""

    __slots__ = ("values", "years", "meta")

    def __init__(self, values, years, meta):
        self.values = values
        self.years = years
        self.meta = meta

    def at(self, month: int, row: int, col: int) -> int:
        return self.values[(month * N_LAT + row) * N_LON + col]

    def years_at(self, month: int, row: int, col: int) -> int:
        return self.years[(month * N_LAT + row) * N_LON + col]


@lru_cache(maxsize=1)
def _load() -> _Grid:
    if not os.path.exists(BIN_PATH):
        raise FileNotFoundError(
            f"Rainfall grid missing at {BIN_PATH}. "
            f"Build it with scripts/build_rainfall_grid.py"
        )

    n = N_MONTHS * N_LAT * N_LON

    with open(BIN_PATH, "rb") as fh:
        raw = fh.read(n * 2)
        years = fh.read(n)

    if len(raw) != n * 2 or len(years) != n:
        raise ValueError("Rainfall grid is truncated or corrupt")

    values = struct.unpack(f"<{n}H", raw)
    year_vals = struct.unpack(f"<{n}B", years)

    with open(META_PATH, "r", encoding="utf-8") as fh:
        meta = json.load(fh)

    return _Grid(values, year_vals, meta)


def is_available() -> bool:
    return os.path.exists(BIN_PATH) and os.path.exists(META_PATH)


def _clamp(v: float, lo: float, hi: float) -> float:
    return hi if v > hi else (lo if v < lo else v)


def sample(lat: float, lon: float) -> RainfallSample:
    """
    Bilinearly interpolate the monthly climatology at (lat, lon).

    Longitude wraps at the antimeridian; latitude is clamped at the
    poles. Neighbouring cells flagged as no-data drop out of the
    weighted mean, and their weight is redistributed.
    """
    g = _load()
    meta = g.meta

    lat = _clamp(float(lat), -90.0, 90.0)
    lon360 = float(lon) % 360.0

    # Continuous indices into the centre arrays.
    row_f = _clamp((LAT_FIRST - lat) / CELL, 0.0, N_LAT - 1)
    col_f = ((lon360 - LON_FIRST) / CELL) % N_LON

    r0 = int(row_f)
    r1 = min(r0 + 1, N_LAT - 1)
    tr = row_f - r0

    c0 = int(col_f)
    c1 = (c0 + 1) % N_LON
    tc = col_f - c0

    corners = (
        (r0, c0, (1 - tr) * (1 - tc)),
        (r0, c1, (1 - tr) * tc),
        (r1, c0, tr * (1 - tc)),
        (r1, c1, tr * tc),
    )

    monthly: list[float] = []
    year_total = 0.0

    for m in range(N_MONTHS):
        total_w = 0.0
        acc = 0.0
        for (r, c, w) in corners:
            v = g.at(m, r, c)
            if v == NO_DATA or w <= 0.0:
                continue
            acc += v * w
            total_w += w

        monthly.append(round(acc / total_w, 2) if total_w > 0 else 0.0)

    # Years of record behind the mean, taken from the nearest centre.
    nr, nc = corners[0][0], corners[0][1]
    year_total = min(
        g.years_at(m, nr, nc) for m in range(N_MONTHS)
    )

    # Nearest cell centre, for provenance.
    cell_lat = round(LAT_FIRST - nr * CELL, 4)
    cell_lon = round((LON_FIRST + nc * CELL) % 360.0, 4)
    if cell_lon > 180.0:
        cell_lon -= 360.0

    interpolated = not (tr == 0.0 and tc == 0.0)

    return RainfallSample(
        monthly_mm=monthly,
        annual_mm=round(sum(monthly), 2),
        cell_lat=cell_lat,
        cell_lon=cell_lon,
        resolution_deg=CELL,
        source=meta.get("source", "NOAA PSL CMAP"),
        period=meta.get("climatology_period", "1991-2020"),
        valid_years=int(year_total),
        interpolated=interpolated,
    )


def scale_to_annual(
    sample_result: RainfallSample, annual_mm: float
) -> RainfallSample:
    """
    Rescale a sample's monthly distribution to a known annual total.

    Keeps the shape the grid provides (which is robust) and adopts a
    locally measured total (which resolves the coarse-grid bias). Used
    when the caller supplies `annual_rainfall_override`.
    """
    current = sum(sample_result.monthly_mm)

    if current <= 0:
        # No usable shape: fall back to a flat distribution.
        monthly = [round(annual_mm / 12.0, 2)] * 12
    else:
        factor = annual_mm / current
        monthly = [round(v * factor, 2) for v in sample_result.monthly_mm]

    # Absorb rounding drift in the wettest month.
    drift = round(annual_mm - sum(monthly), 2)
    if drift:
        wettest = max(range(12), key=lambda i: monthly[i])
        monthly[wettest] = round(monthly[wettest] + drift, 2)

    return RainfallSample(
        monthly_mm=monthly,
        annual_mm=round(sum(monthly), 2),
        cell_lat=sample_result.cell_lat,
        cell_lon=sample_result.cell_lon,
        resolution_deg=sample_result.resolution_deg,
        source=sample_result.source,
        period=sample_result.period,
        valid_years=sample_result.valid_years,
        interpolated=sample_result.interpolated,
        scaled_to_override=True,
    )
