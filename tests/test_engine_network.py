"""Network routing invariants for the pytedi engine.

The existing engine tests use dams that all drain straight to the catchment outlet
(ds_damid = -99), which is the one topology that cannot exercise dam-to-dam routing.
These tests cover dams in series.
"""

import numpy as np
import pandas as pd

from pytedi.main import tedimodel

# damlist columns, in order:
#   dam_id, ds_damid, surfacearea_m2, catchuptotal_km2, catchuplocal_km2, vol_ML,
#   year_start, group_name, demfactor, bypass_MLperT, bypass_start, bypass_end,
#   wfill_MLperT, wfill_start, wfill_end, output


def _two_dams(ds_damid_of_upstream, demfactor=0.0, downstream_local_km2=1.0):
    """A small upstream dam and a large downstream dam.

    Pass ds_damid_of_upstream=2 to put them in series (dam 3 drains into dam 2) or -99 to
    put them in parallel (both drain straight to the outlet). Steady inflow and no climate,
    so the upstream dam fills on the first timestep and spills from then on.
    """
    m = tedimodel()
    m.timestep = "day"
    m.calc_nat_or_obs = "obs"
    m.cat_area_km2 = 10.0

    # dam 2: the large downstream dam
    m.damlist.loc[0] = [2, -99, 5000.0, downstream_local_km2, downstream_local_km2, 50.0,
                        0, "Irrigation", demfactor, 0.0, 101, 1231, 0.0, 101, 1231, 1]
    # dam 3: the small upstream dam
    m.damlist.loc[1] = [3, ds_damid_of_upstream, 1000.0, 1.0, 1.0, 5.0,
                        0, "Irrigation", demfactor, 0.0, 101, 1231, 0.0, 101, 1231, 1]

    idx = pd.date_range("2000-01-01", periods=30, freq="D")
    ts = pd.DataFrame(index=idx)
    ts["rain"] = 0.0
    ts["evap"] = 0.0
    ts["flowup"] = 100.0         # 1 km2 of a 10 km2 catchment -> 10 ML/day
    ts["flowdown"] = np.nan
    ts["Irrigation"] = 0.1       # demand = capacity x demfactor x 0.1 per day
    m.ts = ts
    return m


def test_spill_from_an_upstream_dam_reaches_the_downstream_dam():
    """Dams in series must be connected: everything leaving the upstream dam has to
    arrive at the dam below it, not at the catchment outlet."""
    m = _two_dams(ds_damid_of_upstream=2)
    m.run_model()

    ind = m.indiv_results
    # idam is the internal upstream-to-downstream index, so 0 is the upstream dam
    upstream = ind[ind["idam"] == 0]
    downstream = ind[ind["idam"] == 1]

    assert upstream["outflow"].sum() > 0, "test is only meaningful when the upstream dam releases water"

    np.testing.assert_allclose(
        downstream["updam_spill"].to_numpy(dtype=float),
        upstream["outflow"].to_numpy(dtype=float),
        atol=1e-9,
        err_msg="upstream dam outflow did not arrive at the downstream dam",
    )


def test_a_dam_in_series_supplies_demand_it_could_not_meet_in_parallel():
    """A catchment-level check that needs no per-dam output. The downstream dam is given a
    small local catchment and a demand it cannot satisfy on its own, so routing the upstream
    dam into it must raise total catchment impact. Wired in parallel the two dams only
    intercept their own runoff, and total impact is bounded by capacity plus what each dam
    can supply from its own inflow."""
    kwargs = dict(demfactor=1.0, downstream_local_km2=0.1)

    series = _two_dams(ds_damid_of_upstream=2, **kwargs)
    series.run_model()

    parallel = _two_dams(ds_damid_of_upstream=-99, **kwargs)
    parallel.run_model()

    series_impact = series.catch_results["agg_impact"].sum()
    parallel_impact = parallel.catch_results["agg_impact"].sum()

    assert series_impact > parallel_impact, (
        f"series impact {series_impact:.3f} ML should exceed parallel "
        f"{parallel_impact:.3f} ML, since the downstream dam gains the upstream spill"
    )
