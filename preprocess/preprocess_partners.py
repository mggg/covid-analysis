"""Converts Partners (Harvard/MGH) clinics spreadsheet to a shapefile."""
import os
import click
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from shapely.geometry import Point
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


@click.command()
@click.option('--clinics-xlsx', required=True,
              help='The path of the clinics spreadsheet.')
@click.option('--output-shp', required=True,
              help='The path of the shapefile to be generated.')
def main(clinics_xlsx, output_shp):
    df = pd.read_excel(clinics_xlsx)
    df = df.rename(columns={col: col.lower().replace(' ', '_')
                            for col in df.columns})
    geocode = RateLimiter(Nominatim(user_agent='MGGG covid-analysis').geocode,
                          min_delay_seconds=1)

    geometries = []
    for idx, row in tqdm(enumerate(df.itertuples())):
        loc = geocode({
            'state': getattr(row, 'state'),
            'city': getattr(row, 'city'),
            'address': getattr(row, 'address')
        }, ['US'])
        if loc is None:
            # A few facilities in the 2020-05-27 version of the
            # spreadsheets have incorrect state columns.
            # It's worth retrying without a state specified.
            loc = geocode({
                'city': getattr(row, 'city'),
                'address': getattr(row, 'address')
            }, ['US'])

        if loc is not None:
            geometries.append(Point(*loc[1]))
        else:
            print(f'Warning: could not geocode row {idx}.')
            print(row)
            geometries.append(None)
    df['geometry'] = geometries
    gdf = gpd.GeoDataFrame(df)
    gdf.crs = 'EPSG:4326'  # long/lat projection
    gdf.to_file(output_shp)

if __name__ == '__main__':
    main()
