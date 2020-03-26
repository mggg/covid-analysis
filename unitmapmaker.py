"""
Get selected block group-level data from the ACS 5-year survey.
Author: Nick Doiron (@mapmeld)
"""

import time, json
import requests
from osgeo import ogr

state = '25'
year = '2018'
survey = 'acs/acs5'
unit = 'block group'
shapefile_location "./tl_2010_" + state + "_bg/tl_2010_" + state + "_bg.shp"

counties = []
# https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697
last_county = 27
for fips in range(1, last_county + 1):
    newfips = str(fips)
    while len(newfips) < 3:
        newfips = '0' + newfips
    counties.append(newfips)

cols = {
    'hh_with_65plus': 'B11007_002E'
}

# https://api.census.gov/data/key_signup.html
api_key = '81bae7d10ba7690a0a0d593fbff3bb0f1e8394d7'

block_groups = {}
for county in counties:
    url = 'https://api.census.gov/data/' + year + '/' + survey + '?get=' + ','.join(list(cols.values())) + '&for=' + unit + ':*&in=state:' + state + '+county:' + county + '&key=' + api_key
    resp = requests.get(url)
    # if counties.index(county) == 0:
        # print(resp.text)
    try:
        blocks = resp.json()
        print(county + ": " + str(len(blocks)))
        headers = None
        for block in blocks:
            if headers is None:
                headers = block
            else:
                block_group_fips = block[headers.index('state')] + block[headers.index('county')] + block[headers.index('tract')] + block[headers.index('block group')]
                block_groups[block_group_fips] = {}
                for col in list(cols.keys()):
                    block_groups[block_group_fips][col] = int(block[headers.index(cols[col])])
    except:
        print('fail')
    time.sleep(1)

for item in block_groups.keys():
    fields = block_groups[item].keys()
    break

driver = ogr.GetDriverByName('ESRI Shapefile')
dataSource = driver.Open(shapefile_location, 1) #1 is read/write

layer = dataSource.GetLayer()

print('creating columns')
for field in fields:
    fldDef = ogr.FieldDefn(field, ogr.OFTInteger)
    layer.CreateField(fldDef)

print('setting columns')
feature = layer.GetNextFeature()
while feature:
    geoid = feature.GetField("GEOID")
    if geoid in block_groups:
        for field in fields:
            feature.SetField(field, block_groups[geoid][field])
            layer.SetFeature(feature)
    else:
        print(geoid)
    feature = layer.GetNextFeature()
