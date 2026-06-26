"""Tests for distribution-based dam-population sampling."""

import pandas as pd

from pytedi.damslist import damlist_from_distribution


def _params(seed):
    # half the draws are small (0-1 ML), half are large (10-20 ML)
    return {
        "total_dam_vol_ML": 100.0,
        "vol_surfarea_a": 0.0001042,
        "vol_surfarea_b": 1.3213,
        "damcatch_method": "linear",
        "damdist_table": pd.DataFrame({"id": [1, 2],
                                       "vol_low": [0.0, 10.0],
                                       "vol_high": [1.0, 20.0],
                                       "vol_prob": [0.5, 0.5]}),
        "damcatch_table": pd.DataFrame({"vol_max": [0.0, 5.0, 100.0],
                                        "area_max": [0.0, 0.3, 1.4]}),
        "cat_area_km2": 1000.0,
        "scale_limit": 0.8,
        "seed": seed,
    }


def test_distribution_sums_to_target_exactly_and_keeps_large_dams():
    dl = damlist_from_distribution(_params(0))

    # the population sums to the target volume exactly, with no zero/negative dams
    assert abs(dl["vol_ML"].sum() - 100.0) < 1e-9
    assert (dl["vol_ML"] > 0).all()

    # half the distribution is in the 10-20 ML bin, so large dams must survive
    # (the previous overshoot-trim stripped them off the end of the list)
    assert (dl["vol_ML"] >= 10).sum() >= 1


def test_distribution_is_reproducible_for_a_given_seed():
    a = damlist_from_distribution(_params(7))["vol_ML"].to_list()
    b = damlist_from_distribution(_params(7))["vol_ML"].to_list()
    assert a == b
