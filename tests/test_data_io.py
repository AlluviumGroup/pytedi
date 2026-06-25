"""Round-trip tests for pytedi's native model format (save_model / open_model)."""

import numpy as np
import pandas as pd
import pandas.testing as pdt

from pytedi.main import tedimodel


def _make_minimal_model():
    """A small but complete tedimodel, built in code (no external data)."""
    m = tedimodel()
    m.title = "Round trip test"
    m.timestep = "day"
    m.calc_nat_or_obs = "obs"
    m.cat_area_km2 = 12.5
    m.scale_limit = 0.8
    m.vary_surfarea = False
    m.vol_surfarea_a = 0.0001042
    m.vol_surfarea_b = 1.3213
    m.startstore_propfull = 0.0

    # two dams. The 'output' flag is left NaN for the second dam, as happens for
    # distribution-generated dams in real scenarios (only flagged dams get output=1).
    m.damlist.loc[0] = [1, -99, 1000.0, 2.0, 1.5, 5.0, 0, "Stock&Domestic",
                        0.5, 0.0, 101, 1231, 0.0, 101, 1231, 1]
    m.damlist.loc[1] = [2, 1, 2000.0, 4.0, 2.0, 10.0, 0, "Irrigation",
                        0.8, 0.0, 101, 1231, 0.0, 101, 1231, np.nan]

    # short timeseries
    idx = pd.date_range("2000-01-01", periods=5, freq="D")
    ts = pd.DataFrame(index=idx)
    ts["rain"] = [1.0, 2.0, 3.0, 4.0, 5.0]
    ts["evap"] = [5.0, 4.0, 3.0, 2.0, 1.0]
    ts["flowup"] = [10.0, 20.0, 30.0, 40.0, 50.0]
    ts["flowdown"] = np.nan
    ts["Stock&Domestic"] = 0.1
    ts["Irrigation"] = 0.2
    m.ts = ts

    return m


def test_save_model_then_open_model_roundtrips_inputs(tmp_path):
    original = _make_minimal_model()

    prefix = str(tmp_path / "mymodel")
    original.save_model(prefix)

    reloaded = tedimodel()
    reloaded.open_model(prefix + "_params.scn")

    assert reloaded.title == original.title
    assert reloaded.timestep == original.timestep
    assert reloaded.calc_nat_or_obs == original.calc_nat_or_obs
    assert reloaded.cat_area_km2 == original.cat_area_km2
    assert reloaded.scale_limit == original.scale_limit
    assert reloaded.vary_surfarea == original.vary_surfarea
    assert reloaded.vol_surfarea_a == original.vol_surfarea_a
    assert reloaded.vol_surfarea_b == original.vol_surfarea_b
    assert reloaded.startstore_propfull == original.startstore_propfull

    pdt.assert_frame_equal(
        reloaded.damlist.reset_index(drop=True),
        original.damlist.reset_index(drop=True),
        check_dtype=False,
    )

    pdt.assert_frame_equal(
        reloaded.ts.astype("float64"),
        original.ts.astype("float64"),
        check_dtype=False,
        check_freq=False,
        check_names=False,
    )


def test_converted_model_runs_identically_to_original(tmp_path):
    """The lossless-conversion guarantee: saving to the native format, reloading,
    and running must reproduce the original run exactly (same engine, same inputs)."""
    original = _make_minimal_model()
    original.run_model()

    prefix = str(tmp_path / "mymodel")
    original.save_model(prefix)

    reloaded = tedimodel()
    reloaded.open_model(prefix + "_params.scn")
    reloaded.run_model()

    pdt.assert_frame_equal(reloaded.catch_results, original.catch_results, check_freq=False)
    pdt.assert_frame_equal(reloaded.indiv_results, original.indiv_results, check_freq=False)
