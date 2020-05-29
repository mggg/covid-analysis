"""Helper functions for loading state-level datasets."""
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict
from config import PROJ, path

NATIONAL_DATASETS = {
    'states': 'cb_2018_us_state_500k/cb_2018_us_state_500k.shp',
    'hospitals': 'Hospitals/Hospitals.shp',
    'ed_inst': 'Colleges_and_Universities/Colleges_and_Universities.shp'
}

MA_DATASETS = {
    'acute_care': 'MA_Hospitals/Originals/acute_care_hospitals/HOSPITALS_PT.shp',
    'non_acute_care': 'MA_Hospitals/Originals/non_acute_care_hospitals/HOSPITALS_NONACUTE_PT.shp',
    'ed_inst': 'MA_Universities/SHP_dormcap/ma_universities.shp'
}

# Special cases to handle in MA (not necessarily completely filtered out)
MA_IRREGULAR_COLLEGES = [
    'Northeastern University',
    'Boston College',
    'University of Massachusetts Dartmouth Center for Innovation and Entrepreneurship'
]

TRAVEL_TIME_DATASETS = {
    state: f'travel_times/{state}_pairwise_distances_with_names.csv'
    for state in ('CA', 'MI', 'NY')
}


def load_states():
    """Loads a shapefile of state boundaries."""
    return gpd.read_file(path(NATIONAL_DATASETS['states']))


def load_state_data(state_code: str,
                    min_dorm_beds: int = 1,
                    min_hosp_beds: int = 1,
                    prefer_travel_time: bool = False,
                    acute_care_only: bool = False) -> Dict:
    """Loads basic hospital and educational institution data for a state.

    :param state_code: The state's two-letter postal code.
    :param min_dorm_beds: The minimum number of dorm beds necessary for an
        educational institution's inclusion. At a minimum, institutions
        with zero dorm beds (pure commuter schools) should be filtered out.f
    :param min_hosp_beds: The minimum number of dorm beds necessary for an
        hospital's inclusion. At a minimum, hospitals with zero
        or negative beds should be filtered out.
    :param prefer_travel_time: If available, use travel times (in minutes)
        for distance calculations instead of Euclidean distance.
    :param acute_care_only: Only include hospitals that are explicitly
        labeled as acute-care hospitals.
    :return: A dictionary of datasets and pairwise distances.
    """
    state_code = state_code.upper()
    states_gdf = load_states()
    outline_gdf = states_gdf[states_gdf['STUSPS'] == state_code]
    outline_gdf = outline_gdf.to_crs(PROJ).reset_index().copy()

    hospitals_gdf = load_hospitals(state_code, min_hosp_beds, acute_care_only)
    ed_inst_gdf = load_ed_inst(state_code, min_dorm_beds)

    # Get pairwise distances.
    if prefer_travel_time and state_code in TRAVEL_TIME_DATASETS:
        distance_metric = 'travel_time'
        travel_time_df = pd.read_csv(path(TRAVEL_TIME_DATASETS[state_code]))
        travel_time_df = travel_time_df.rename(columns={
            **{col: col.strip() for col in travel_time_df.columns},
            ' Driving Time (s)': 'Time'
        })
        distances = travel_time_distances(travel_time_df,
                                          hospitals_gdf,
                                          ed_inst_gdf)
    else:
        distance_metric = 'euclidean'
        distances = euclidean_distances(hospitals_gdf, ed_inst_gdf)

    return {
        'outline': outline_gdf,
        'ed_inst': ed_inst_gdf,
        'hospitals': hospitals_gdf,
        'distances': distances,
        'distance_metric': distance_metric
    }


def load_hospitals(state_code: str,
                   min_hosp_beds: int,
                   acute_care_only: bool) -> gpd.GeoDataFrame:
    """Loads filtered hospital data for a state."""
    if state_code == 'MA':
        # MA: Use state-specific hospital/university datasets.
        acute_care_gdf = gpd.read_file(path(MA_DATASETS['acute_care']))
        non_acute_care_gdf = gpd.read_file(path(MA_DATASETS['non_acute_care']))
        acute_care_gdf['ACUTE'] = True
        acute_care_gdf = acute_care_gdf.to_crs(PROJ)
        if acute_care_only:
            hospitals_gdf = acute_care_gdf.drop(columns=set(acute_care_gdf.columns) -
                                                set(non_acute_care_gdf.columns))
        else:
            non_acute_care_gdf['ACUTE'] = False
            non_acute_care_gdf = non_acute_care_gdf.to_crs(PROJ)
            non_acute_care_gdf = non_acute_care_gdf.rename(columns={'FAC_NAME':
                                                                    'SHORTNAME'})
            hospitals_gdf = gpd.GeoDataFrame(pd.concat([
                acute_care_gdf,
                non_acute_care_gdf
            ])).drop(columns=set(acute_care_gdf.columns) -
                     set(non_acute_care_gdf.columns)) \
               .rename(columns={'SHORTNAME': 'NAME', 'BEDCOUNT': 'BEDS'})
            hospitals_gdf.crs = PROJ
        # Filter out islands.
        hospitals_gdf = hospitals_gdf[(hospitals_gdf['TOWN'] != 'Oak Bluffs') &
                                      (hospitals_gdf['TOWN'] != 'Nantucket')]
        # Filter out psychiatric hospitals.
        # (Other non-acute hospitals may be retained.)
        # Moon: Filter out Lawrence Memorial.
        hospitals_gdf = hospitals_gdf[
            (hospitals_gdf['COHORT'] != 'Psychiatric Hospital') &
            (hospitals_gdf['NAME'] != 'Corrigan Mental Health Center') &
            (hospitals_gdf['NAME'] != 'Lawrence Memorial Hospital of Medford') 
        ]
        # Hospital systems should be a category. (TODO: other fields here)
        hospitals_gdf['HOSPSYSTEM'] = hospitals_gdf['HOSPSYSTEM'].astype('category')
    else:
        all_hospitals_gdf = gpd.read_file(path(NATIONAL_DATASETS['hospitals']))
        hospitals_gdf = all_hospitals_gdf[all_hospitals_gdf['STATE'] == state_code]
        hospitals_gdf = hospitals_gdf.copy()
        hospitals_gdf['ACUTE'] = True
        acute_rows = (hospitals_gdf['TYPE'] == 'GENERAL ACUTE CARE')
        hospitals_gdf.loc[~acute_rows, 'ACUTE'] = False
        if acute_care_only:
            hospitals_gdf = hospitals_gdf[acute_rows]
        hospitals_gdf = hospitals_gdf.to_crs(PROJ)

    hospitals_gdf = hospitals_gdf[hospitals_gdf['BEDS'] >= min_hosp_beds]
    return hospitals_gdf.reset_index().copy()


def load_ed_inst(state_code: str, min_dorm_beds: int) -> gpd.GeoDataFrame:
    """Loads filtered educational institution data for a state."""
    if state_code == 'MA':
        # MA: Use state-specific hospital/university datasets.
        ed_inst_gdf = gpd.read_file(path(MA_DATASETS['ed_inst']))
        # Fix irregularities in NEU data and remove satellite BC/UMD campuses.
        ed_inst_gdf = ed_inst_gdf[~ed_inst_gdf['COLLEGE'].isin(MA_IRREGULAR_COLLEGES) |
                                  (ed_inst_gdf['CAMPUS'] == 'Main Campus')]
        # HMS name cleanup to make maps more interpretable
        ed_inst_gdf['COLLEGE'] = ed_inst_gdf['COLLEGE'].replace({
            'Harvard University': 'Harvard Medical School'
        })
        ed_inst_gdf = ed_inst_gdf.rename(columns={'DORMCAP': 'DORM_CAP'})
    else:
        # Non-MA: Use national hospital/university datasets.
        all_ed_inst_gdf = gpd.read_file(path(NATIONAL_DATASETS['ed_inst']))
        ed_inst_gdf = all_ed_inst_gdf[all_ed_inst_gdf['STATE'] == state_code]
    ed_inst_gdf = ed_inst_gdf.to_crs(PROJ)
    ed_inst_gdf = ed_inst_gdf[ed_inst_gdf['DORM_CAP'] >= min_dorm_beds]
    return ed_inst_gdf.reset_index().copy()


def euclidean_distances(hospitals_gdf: gpd.GeoDataFrame,
                        ed_inst_gdf: gpd.GeoDataFrame) -> np.ndarray:
    """Calculates pairwise Euclidean distances."""
    distances = np.zeros((len(hospitals_gdf), len(ed_inst_gdf)))
    for hosp_idx, hosp_row in enumerate(hospitals_gdf.itertuples()):
        for ed_idx, ed_row in enumerate(ed_inst_gdf.itertuples()):
            dist = hosp_row.geometry.distance(ed_row.geometry)
            distances[hosp_idx, ed_idx] = dist
    return distances


def travel_time_distances(travel_time_df: pd.DataFrame,
                          hospitals_gdf: gpd.GeoDataFrame,
                          ed_inst_gdf: gpd.GeoDataFrame,
                          epsilon: float = 1e-4,
                          default_time: float = 10000) -> np.ndarray:
    """Loads precomputed pairwise travel time distances.

    :param travel_time_df: The precomputed table of pairwise travel times
        (in Olivia Walch's format).
    :param hospitals_gdf: Hospitals to calculate travel times for.
    :param ed_inst_gdf: Educational institutions to calculate travel times for.
    :param epsilon: The tolerance used for matching longitudes and latitudes.
    :param default_time: The default time to use when a (hospital,
         educational institution) pair is missing from the travel time data.
    :return: A pairwise distance matrix (rows are hospitals, columns are
        educational institutions).
    """
    times = default_time * np.ones((len(hospitals_gdf), len(ed_inst_gdf)))
    travel_time_index = {}
    for row in travel_time_df.itertuples():
        source = getattr(row, 'Source')
        dest = getattr(row, 'Destination')
        travel_time = getattr(row, 'Time') / 60
        travel_time_index[f'{source} -> {dest}'] = travel_time

    for hosp_idx, hosp_row in enumerate(hospitals_gdf.itertuples()):
        for ed_idx, ed_row in enumerate(ed_inst_gdf.itertuples()):
            # Try to match based on name, and then disambiguate based on long/lat.
            ed_name = getattr(ed_row, 'NAME').replace(',', '')
            hosp_name = getattr(hosp_row, 'NAME').replace(',', '')
            if f'{ed_name} -> {hosp_name}' in travel_time_index:
                travel_time = travel_time_index[f'{ed_name} -> {hosp_name}']
            else:
                ed_lat = getattr(ed_row, 'LATITUDE')
                ed_long = getattr(ed_row, 'LONGITUDE')
                hosp_lat = getattr(hosp_row, 'LATITUDE')
                hosp_long = getattr(hosp_row, 'LONGITUDE')
                df = travel_time_df
                travel_row = df[((df['SourceLat'] - ed_lat).abs() <= epsilon) &
                                ((df['SourceLong'] - ed_long).abs() <= epsilon) &
                                ((df['DestLat'] - hosp_lat).abs() <= epsilon) &
                                ((df['DestLong'] - hosp_long).abs() <= epsilon)]
                if not travel_row.empty:
                    if len(travel_row) > 1:
                        print('Warning:', ed_name, '->', hosp_name, 'ambiguous')
                    travel_time = travel_row['Time'].iloc[0] / 60
                else:
                    print('Warning: could not find travel time for',
                          f'{ed_name} -> {hosp_name}')
                    continue
            times[hosp_idx, ed_idx] = travel_time
    return times
