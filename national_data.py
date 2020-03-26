import geopandas as gpd

DATASETS = {
    'states': 'data/cb_2018_us_state_500k/cb_2018_us_state_500k.shp',
    'hospitals': 'data/Hospitals/Hospitals.shp',
    'ed_inst': 'data/Colleges_and_Universities/Colleges_and_Universities.shp'
}

def get_proj(utm_zone):
    return f'+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs'

def load_state_data(state_name, state_code, utm_zone, min_dorm_beds=1):
    """Loads basic hospital and educational institution data for a state."""
    proj = get_proj(utm_zone)
    states_gdf = gpd.read_file(DATASETS['states'])
    outline_gdf = states_gdf[states_gdf['NAME'] == state_name].to_crs(proj)
    all_ed_inst_gdf = gpd.read_file(DATASETS['ed_inst'])
    ed_inst_gdf = all_ed_inst_gdf[all_ed_inst_gdf['STATE'] == state_code].to_crs(proj)
    all_hospitals_gdf = gpd.read_file(DATASETS['hospitals'])
    hospitals_gdf = all_hospitals_gdf[all_hospitals_gdf['STATE'] == state_code].to_crs(proj)
    
    # bed count filtering
    hospitals_gdf = hospitals_gdf[hospitals_gdf['BEDS'] > 0]
    ed_inst_gdf = ed_inst_gdf[ed_inst_gdf['DORM_CAP'] >= min_dorm_beds]
    
    # match original MA analysis nomenclature
    ed_inst_gdf = ed_inst_gdf.rename(columns={'DORM_CAP': 'DORMCAP'})
    hospitals_gdf = hospitals_gdf.rename(columns={'BEDS': 'BEDCOUNT'})

    return {
        'outline': outline_gdf.reset_index(),
        'ed_inst': ed_inst_gdf.reset_index(),
        'hospitals': hospitals_gdf.reset_index()
    }