#!/usr/bin/env python3
"""
Build the compact rainfall climatology raster shipped in data/.

SOURCE DATA
-----------
NOAA PSL CMAP (CPC Merged Analysis of Precipitation) long-term monthly
climatology, 1991-2020 -- a public-domain NOAA product gridded at
2.5 degrees (72 lat x 144 lon).

  https://psl.noaa.gov/data/gridded/data.cmap.html
  https://downloads.psl.noaa.gov/Datasets/cmap/enh/precip.mon.ltm.nc

CMAP merges gauge observations with satellite estimates (GPI, OPI,
SSM/I, AMSU) so it has genuine global coverage -- including ocean and
desert, where gauge-only products are undefined.

WHY NOT IMD 0.25 / CHIRPS?
--------------------------
They are better over India but India-only. Earlier this project used
ten hand-written lat/lon boxes plus a 1100 mm catch-all, so any
coordinate outside India silently received an Indian monsoon profile.
A global raster removes that failure mode entirely. See
services/rainfall_grid.py for the documented resolution trade-off.

USAGE
-----
    python3 scripts/build_rainfall_grid.py --sqlite /path/to/precip_grid.sqlite
    python3 scripts/build_rainfall_grid.py --netcdf /path/to/precip.mon.ltm.nc

The NetCDF path is the reproducible route straight from NOAA (needs
h5py + netcdf access); the SQLite path builds from a pre-packaged
mirror of the same data.
"""
import argparse
import json
import struct
from datetime import date
from pathlib import Path

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

N_LAT = 72
N_LON = 144
N_MONTHS = 12
CELL = 2.5

OUT_BIN = Path(__file__).resolve().parent.parent / "data" / "precip_climatology.bin"
OUT_JSON = Path(__file__).resolve().parent.parent / "data" / "precip_climatology.json"


def lat_centers():
    # CMAP centres run +88.75 (north) down to -88.75 (south).
    return [90.0 - CELL / 2 - i * CELL for i in range(N_LAT)]


def lon_centers():
    # CMAP uses a 0..360 convention with centres at 1.25, 3.75, ...
    return [CELL / 2 + j * CELL for j in range(N_LON)]


def from_sqlite(path: Path):
    import sqlite3

    con = sqlite3.connect(str(path))
    meta = dict(con.execute("SELECT key, value FROM meta").fetchall())

    precip = [[[0.0] * N_LON for _ in range(N_LAT)] for _ in range(N_MONTHS)]
    years = [[[0] * N_LON for _ in range(N_LAT)] for _ in range(N_MONTHS)]

    lats = lat_centers()
    lons = lon_centers()

    # Map cell centre -> (row, col) index.
    row_of = {round(v, 4): i for i, v in enumerate(lats)}
    col_of = {round(v, 4): j for j, v in enumerate(lons)}

    rows = con.execute(
        """
        SELECT c.lat_center, c.lon_center, m.month,
               m.precip_mm_day, m.precip_mm_month, m.valid_yr_count
        FROM cells c JOIN monthly_precip m ON m.cell_id = c.id
        """
    )
    count = 0
    for lat, lon, month, mm_day, mm_month, vyc in rows:
        # The packaged table stores longitude in a -180..180
        # convention; the binary we emit uses CMAP's native 0..360.
        i = row_of.get(round(float(lat), 4))
        j = col_of.get(round(float(lon) % 360.0, 4))
        if i is None or j is None:
            continue

        value = mm_month
        if value is None:
            value = float(mm_day) * DAYS_IN_MONTH[month - 1]

        mi = month - 1
        precip[mi][i][j] = float(value)
        years[mi][i][j] = int(vyc or 0)
        count += 1

    con.close()

    if count != N_MONTHS * N_LAT * N_LON:
        raise SystemExit(f"expected 124416 values, read {count}")

    period = meta.get("climatology_period", "1991/01/01 - 2020/12/31")
    return precip, years, period


def from_netcdf(path: Path):
    import h5py
    import numpy as np

    with h5py.File(str(path), "r") as f:
        lat = f["lat"][:].astype(float)
        lon = f["lon"][:].astype(float)
        raw = f["precip"][:].astype(float)      # (12, 72, 144) mm/day
        missing = float(f["precip"].attrs["missing_value"][0])
        vyc = f["valid_yr_count"][:]
        period = f["time"].attrs["climo_period"].decode()

    raw[raw == missing] = np.nan

    lats = lat_centers()
    lons = lon_centers()
    row_of = {round(v, 4): i for i, v in enumerate(lats)}
    col_of = {round(v, 4): j for j, v in enumerate(lons)}

    precip = [[[0.0] * N_LON for _ in range(N_LAT)] for _ in range(N_MONTHS)]
    years = [[[0] * N_LON for _ in range(N_LAT)] for _ in range(N_MONTHS)]

    for mi in range(N_MONTHS):
        for i, la in enumerate(lat):
            ri = row_of.get(round(float(la), 4))
            if ri is None:
                continue
            for j, lo in enumerate(lon):
                cj = col_of.get(round(float(lo) % 360, 4))
                if cj is None:
                    continue
                v = raw[mi, i, j]
                precip[mi][ri][cj] = (
                    0.0 if v != v else float(v) * DAYS_IN_MONTH[mi]
                )
                years[mi][ri][cj] = int(vyc[mi, i, j])

    return precip, years, period


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite")
    ap.add_argument("--netcdf")
    args = ap.parse_args()

    if args.netcdf:
        precip, years, period = from_netcdf(Path(args.netcdf))
    elif args.sqlite:
        precip, years, period = from_sqlite(Path(args.sqlite))
    else:
        raise SystemExit("pass --sqlite or --netcdf")

    OUT_BIN.parent.mkdir(parents=True, exist_ok=True)

    # Month-major, then row (north -> south), then column (west -> east).
    with OUT_BIN.open("wb") as fh:
        for mi in range(N_MONTHS):
            for i in range(N_LAT):
                for j in range(N_LON):
                    mm = precip[mi][i][j]
                    if mm != mm or mm < 0:      # NaN -> no data
                        fh.write(struct.pack("<H", 65535))
                    else:
                        fh.write(struct.pack("<H", min(int(round(mm)), 65534)))
        for mi in range(N_MONTHS):
            for i in range(N_LAT):
                fh.write(struct.pack(f"<{N_LON}B", *years[mi][i]))

    meta = {
        "source": "NOAA PSL CMAP (CPC Merged Analysis of Precipitation)",
        "source_url": "https://psl.noaa.gov/data/gridded/data.cmap.html",
        "product": "precip.mon.ltm (long-term monthly means)",
        "license": "Public domain (US Government work)",
        "variable": "precipitation rate, converted to monthly total mm",
        "climatology_period": period,
        "grid": {
            "cell_size_deg": CELL,
            "n_lat": N_LAT,
            "n_lon": N_LON,
            "n_months": N_MONTHS,
            "lat_centers_first": lat_centers()[0],
            "lat_centers_last": lat_centers()[-1],
            "lat_order": "descending (north -> south)",
            "lon_convention": "0..360, centre of first cell = 1.25E",
            "lon_centers_first": lon_centers()[0],
        },
        "layout": "uint16 little-endian, month-major then row-major; "
                  "65535 = no data. Followed by one uint8 valid_yr_count "
                  "per grid value in the same order.",
        "built": date.today().isoformat(),
        "builder": "scripts/build_rainfall_grid.py",
    }
    OUT_JSON.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    size = OUT_BIN.stat().st_size
    print(f"wrote {OUT_BIN}  ({size/1024:.0f} KB)")
    print(f"wrote {OUT_JSON}")
    print(f"climatology period: {period}")


if __name__ == "__main__":
    main()
