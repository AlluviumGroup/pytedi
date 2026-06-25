"""Tests for pytedi.climate input-file reading."""

import logging

from pytedi.climate import read_STEDI_clim


def test_read_stedi_clim_falls_back_to_scn_dir_for_dead_absolute_path(tmp_path, caplog):
    """STEDI .scn files often reference dead absolute paths (e.g. a former
    'S:\\...' network drive) while the real input file sits beside the .scn.
    When the absolute path does not exist, read_STEDI_clim should fall back to
    <scn_dir>/<basename> rather than raising, and warn that it inferred a path.
    """
    # the real climate/flow file, sitting beside the (notional) .scn
    real = tmp_path / "F1_flow"
    real.write_text("!date flow\n19000101    1.5\n19000102    2.5\n")

    # the scenario references a dead absolute path whose basename matches
    dead = tmp_path / "drive_that_does_not_exist" / "F1_flow"
    assert dead.is_absolute() and not dead.exists()

    with caplog.at_level(logging.WARNING, logger="pytedi.climate"):
        series = read_STEDI_clim(str(dead), 1, "day", tmp_path)

    assert series.astype(float).tolist() == [1.5, 2.5]
    assert any("inferring" in r.message for r in caplog.records)
