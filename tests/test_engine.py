"""Engine invariants for pytedi."""

import numpy as np
import pandas as pd

from pytedi.main import tedimodel


def _model_with_active_bypass():
    """A one-dam catchment in forward (obs) mode with a low-flow bypass active
    all year, so bp_sum > 0 on every timestep."""
    m = tedimodel()
    m.title = "Bypass invariant"
    m.timestep = "day"
    m.calc_nat_or_obs = "obs"
    m.cat_area_km2 = 10.0

    # one dam: 2 km2 local catchment, 5 ML capacity, 1 ML/day bypass all year
    m.damlist.loc[0] = [1, -99, 500.0, 2.0, 2.0, 5.0, 0, 9999, "Irrigation",
                        0.5, 1.0, 101, 1231, 0.0, 101, 1231, 1]

    idx = pd.date_range("2000-01-01", periods=10, freq="D")
    ts = pd.DataFrame(index=idx)
    ts["rain"] = 0.0
    ts["evap"] = 0.0
    ts["flowup"] = 10.0          # steady inflow upstream of the dams
    ts["flowdown"] = np.nan
    ts["Irrigation"] = 0.1
    m.ts = ts
    return m


def test_catchment_impact_equals_nodams_minus_withdams_with_bypass():
    """Impact is defined (as in Windows STEDI) as Q-NoDams - Q-WithDams. Bypass
    flow already reaches the outlet (it is part of flow_down), so it must NOT be
    subtracted a second time."""
    m = _model_with_active_bypass()
    m.run_model()
    cr = m.catch_results

    assert cr["bp"].sum() > 0, "test is only meaningful when bypass is active"
    np.testing.assert_allclose(
        cr["agg_impact"].to_numpy(dtype=float),
        (cr["flow_up"] - cr["flow_down"]).to_numpy(dtype=float),
        atol=1e-9,
    )
