import numpy as np
import pandas as pd
import geopandas as gpd
import os.path
from typing import Dict

CLINIC_DATASETS = {
    'clia-cert-affil': '../data/clinics/2020-06-01-CLIACertificates-Affiliation.csv',
    'clia-cert-alpha': '../data/clinics/2020-06-01-CLIACertificates-Alpha.csv'
    #'partners': '../data/Partners_raw/Clinical.xlsx'
}

# clia, name, address, lat, lon



def read_clinic_dsets() -> list:
    dataframes = []
    for dataset in CLINIC_DATASETS:
        filename = CLINIC_DATASETS[dataset]
        ext = get_filetype(filename)
        if ext == ".csv":
            dataframes.append(pd.read_csv(filename))
        elif ext == ".xlsx":
            dataframes.append(pd.read_excel(filename))
        else:
            raise Exception("Error: unable to read file.")
    return dataframes

def merge_clinics(dataframes) -> Dict:
    clinics = {}
    for df in dataframes:
        clia_col = df['clia']
        for i in range(0, clia_col.size):
            clia = clia_col[i]
            if clia not in clinics:
               clinics[clia] = [df.at[i, 'name'], 
                                df.at[i, 'address'],
                                df.at[i, 'latitude'],
                                df.at[i, 'longitude']]
    return clinics


#################
# Helpers       #
#################
def get_filetype(filename) -> str:
        ext = ""
        if os.path.isfile(filename):
                ext = os.path.splitext(filename)[-1].lower()
        else:
                raise Exception("\'{}\' is not a file.".format(filename))
        return ext


#################
# Calls         #
#################
def run_merge():
    unique_clinics = merge_clinics(read_clinic_dsets())
    non_clia_clinics = {}

    for i in range(0, 40): # randomly set 40 clinics as non-clia for testing
        key, val = unique_clinics.popitem()
        non_clia_clinics[key] = val

    data = {} # clia, name, address, lat, lon
    index = 0
    for clinic in unique_clinics:
        unique_clinics[clinic].insert(0, clinic)
        data[index] = unique_clinics[clinic]
        index += 1
    for clinic in non_clia_clinics:
        non_clia_clinics[clinic].insert(0, "NaN")
        data[index] = non_clia_clinics[clinic]
        index += 1

    data_df = pd.DataFrame.from_dict(data, orient='index', 
                columns=['clia', 'name', 'address', 'lat', 'lon'])

    data_df.to_excel("test-data/test-clia-file.xlsx")

run_merge()


