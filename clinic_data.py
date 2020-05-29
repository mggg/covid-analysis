"""Helper functions for loading clinic/testing facility data."""
# TODO: Currently, we only have data for the Partners.
# We will be adding Tufts, etc. shortly.

import geopandas as gpd
from config import PROJ, path

CLINIC_DATASETS = {
    'partners': 'health_systems/partners/partners.shp'
}

def load_clinic_data(systems=None) -> gpd.GeoDataFrame:
    """Loads clinic data for all available health systems (or a subset).

    :param systems: The health care systems to load data for.
        If None, data is loaded for all available systems.
    :return: A single :class:`gpd.GeoDataFrame` with data for all
        specified systems.
    """
    if systems is None:
        return gpd.GeoDataFrame(path(CLINIC_DATASETS['partners']))
    gdfs = []
    for system in systems:
        if system.lower() in CLINIC_DATASETS:
            gdfs.append(gpd.GeoDataFrame(path(CLINIC_DATASETS[system.lower()])))
        else:
            print(f'Warning: system {system} not found. Skipping...')
    if gdfs:
        return gdfs[0]  # TODO: merge
    return None

