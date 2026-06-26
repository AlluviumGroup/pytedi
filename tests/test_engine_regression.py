"""Golden-output regression for the TEDI engine.

Pins the catchment water-balance results for a small obs-mode (forward) and
nat-mode (bisection) model so that performance refactors of the engine (e.g.
re-enabling numba @jit on the timestep loops) can be verified to produce
identical results.

Golden values were captured from the current engine (numba @jit timestep loops +
the corrected catchment-outlet surface area). Refresh them whenever the engine's
results change by design.
"""

import numpy as np
import pandas as pd

from pytedi.main import tedimodel


def _build(calc):
    m = tedimodel()
    m.title = "golden"
    m.timestep = "day"
    m.calc_nat_or_obs = calc
    m.cat_area_km2 = 12.0
    m.damlist.loc[0] = [1, -99, 1500.0, 3.0, 3.0, 8.0, 0, "Irrigation", 0.6, 0.0, 101, 1231, 0.0, 101, 1231, 1]
    m.damlist.loc[1] = [2, -99, 800.0, 2.0, 2.0, 4.0, 0, "Stock", 0.4, 0.0, 101, 1231, 0.0, 101, 1231, 1]
    idx = pd.date_range("2000-01-01", periods=12, freq="D")
    ts = pd.DataFrame(index=idx)
    ts["rain"] = [0, 5, 12, 0, 0, 3, 20, 0, 0, 8, 0, 1.0]
    ts["evap"] = [6, 5, 4, 6, 7, 5, 3, 6, 6, 4, 6, 5.0]
    flow = np.array([0, 0, 2, 15, 40, 5, 1, 30, 8, 0, 0, 3.0])
    if calc == "obs":
        ts["flowup"] = flow
        ts["flowdown"] = np.nan
    else:
        ts["flowdown"] = flow
        ts["flowup"] = np.nan
    ts["Irrigation"] = 0.15
    ts["Stock"] = 0.05
    m.ts = ts
    return m


GOLDEN = {
    "obs": {
        "flow_up":    [0.0, 0.0, 2.0, 15.0, 40.0, 5.0, 1.0, 30.0, 8.0, 0.0, 0.0, 3.0],
        "flow_down":  [0.0, 0.0, 1.166667, 8.75, 32.879833, 4.1954, 0.6836, 28.7417, 7.1862, 0.0, 0.0, 2.0052],
        "agg_impact": [0.0, 0.0, 0.833333, 6.25, 7.120167, 0.8046, 0.3164, 1.2583, 0.8138, 0.0, 0.0, 0.9948],
        "estore":     [0.0, 0.0, 0.259733, 5.695933, 12.0, 12.0, 11.5555, 12.0, 12.0, 11.2092, 10.3954, 10.581],
    },
    "nat": {
        "flow_up":    [0.0, 0.0, 3.421875, 24.770508, 43.222656, 5.800781, 1.421875, 31.157227, 8.828125, 0.0, 0.0, 4.324219],
        "flow_down":  [0.0, 0.0, 1.996094, 14.989793, 40.017652, 4.996181, 1.000006, 30.004395, 8.014325, 0.0, 0.0, 2.998364],
        "agg_impact": [0.0, 0.0, 1.425781, 9.780714, 3.205004, 0.8046, 0.421869, 1.152831, 0.8138, 0.0, 0.0, 1.325855],
        "estore":     [0.0, 0.0, 0.644181, 9.611096, 12.0, 12.0, 11.660969, 12.0, 12.0, 11.2092, 10.3954, 10.912055],
    },
}


def test_engine_obs_matches_golden():
    m = _build("obs")
    m.run_model()
    for col, expected in GOLDEN["obs"].items():
        np.testing.assert_allclose(m.catch_results[col].to_numpy(dtype=float), expected, atol=1e-6,
                                   err_msg=f"obs column {col} changed")


def test_engine_nat_matches_golden():
    m = _build("nat")
    m.run_model()
    for col, expected in GOLDEN["nat"].items():
        np.testing.assert_allclose(m.catch_results[col].to_numpy(dtype=float), expected, atol=1e-6,
                                   err_msg=f"nat column {col} changed")
