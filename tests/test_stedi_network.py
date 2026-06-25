"""Tests for importing an explicit dam network from a Windows STEDI .out file."""

from pytedi.scenario import read_STEDI_network_output, full_group_name


# A minimal STEDI .out node table: an outlet, two dams (dam 3 flows into dam 2,
# dam 2 flows to the outlet), then a TOTALS row and the start of the daily block.
OUT_FIXTURE = """ STEDI detailed calculation output

   Node  Type      Next Node   Surface  Farm Dam      Free Impounded     Total   % Total    Bypass    Bypass     Wfill    Demand   Results
                   Downstrea      Area  Capacity      Area      Area      Area    Inflow  Present?  Capacity      Rate     Group     Group
      1  Outlet            0                          8.52      7.13     15.65    54.435
      2  Dam               1    1000.0     5.000      0.00      0.00      8.00     2.000         T    0.1000    0.2000 GroupA GroupA
      3  Dam               2    2000.0    10.000      0.00      0.00      5.00     1.000         F    0.0000    0.0000 GroupB GroupB
 TOTALS                       3000.0    15.000     15.65                       100.000

      Day Rainfall Potential
 19000101     0.00      6.77      0.00
"""


def test_read_stedi_network_output_parses_dams_topology_and_areas(tmp_path):
    out = tmp_path / "F1_out.out"
    out.write_text(OUT_FIXTURE)

    dl = read_STEDI_network_output(str(out)).set_index("dam_id")

    # only the two dams (outlet, TOTALS and daily rows excluded)
    assert list(dl.index) == [2, 3]

    # dam 2 flows to the outlet -> -99; its local area excludes upstream dam 3
    assert dl.loc[2, "ds_damid"] == -99
    assert dl.loc[2, "surfacearea_m2"] == 1000.0
    assert dl.loc[2, "vol_ML"] == 5.0
    assert dl.loc[2, "catchuptotal_km2"] == 8.0
    assert dl.loc[2, "catchuplocal_km2"] == 3.0          # 8.0 - 5.0 (dam 3 upstream)
    assert dl.loc[2, "group_name"] == "GroupA"
    assert dl.loc[2, "bypass_MLperT"] == 0.1
    assert dl.loc[2, "wfill_MLperT"] == 0.2

    # dam 3 flows into dam 2 (a real network link), local == total (nothing upstream)
    assert dl.loc[3, "ds_damid"] == 2
    assert dl.loc[3, "catchuptotal_km2"] == 5.0
    assert dl.loc[3, "catchuplocal_km2"] == 5.0


def test_full_group_name_resolves_truncated_out_labels():
    full = ["Stock&Domestic", "Irrigation"]
    # the .out node table truncates group names
    assert full_group_name("Stock&Dom", full) == "Stock&Domestic"
    assert full_group_name("Irrigatio", full) == "Irrigation"
    # an exact name passes through unchanged
    assert full_group_name("Irrigation", full) == "Irrigation"
    # an unknown label is returned as-is rather than guessed
    assert full_group_name("Vineyard", full) == "Vineyard"
