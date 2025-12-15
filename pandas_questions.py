"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv("data/referendum.csv", sep=";")
    regions = pd.read_csv("data/regions.csv")
    departments = pd.read_csv("data/departments.csv")

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """

    reg = regions.copy()
    dep = departments.copy()

    reg = reg.rename(columns={"code": "code_reg", "name": "name_reg"})
    dep = dep.rename(columns={"code": "code_dep", "name": "name_dep"})
    res = pd.merge(left=reg, right=dep, left_on="code_reg", right_on="region_code")

    return res[["code_reg", "name_reg", "code_dep", "name_dep"]]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    ref = referendum.copy()
    areas = regions_and_departments.copy()

    is_digits = ref["Department code"].str.fullmatch(r"\d+")
    ref.loc[is_digits, "Department code"] = ref.loc[is_digits, "Department code"].str.zfill(2)

    ref = ref[~ref["Department code"].str.contains("Z", na=False)]

    merged = ref.merge(areas, left_on="Department code", right_on="code_dep", how="inner")

    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """

    cols = ["Registered", "Abstentions", "Null", "Choice A", "Choice B"]
    df = referendum_and_areas.copy()

    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    res = (
        df.groupby(["code_reg", "name_reg"], as_index=False)[cols]
          .sum()
          .set_index("code_reg")
    )

    return res[["name_reg"] + cols]


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """

    gdf_regions = gpd.read_file("data/regions.geojson")

    gdf_regions = gdf_regions.rename(columns={"code": "code_reg"})
    gdf_regions["code_reg"] = gdf_regions["code_reg"].astype(str).str.strip()

    rr = referendum_result_by_regions.copy()
    rr.index = rr.index.astype(str).str.strip()

    expressed = rr["Choice A"] + rr["Choice B"]
    rr["ratio"] = (rr["Choice A"] / expressed).fillna(0)

    gdf = gdf_regions.merge(
        rr[["name_reg", "Registered", "Abstentions", "Null", "Choice A", "Choice B", "ratio"]],
        left_on="code_reg",
        right_index=True,
        how="left",
    )

    if "nom" in gdf.columns:
        gdf = gdf.drop(columns=["nom"])

    ax = gdf.plot(column="ratio", legend=True)
    ax.set_axis_off()
    plt.tight_layout()

    return gdf
