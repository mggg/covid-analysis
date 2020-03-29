import json
import requests
import pandas as pd

SOURCE = 'https://static01.nyt.com/newsgraphics/2020/01/21/china-coronavirus/c3dddd29268dcabf8aff59b38d8f8fffabffc710/build/js/chunks/model-lite.js'

if __name__ == '__main__':
    raw = requests.get(SOURCE).text
    
    county_lines = ['[']
    in_counties = False
    for line in raw.split('\n'):
        if 'var us_counties = [' in line:
            in_counties = True
        elif in_counties and '];' in line:
            break
        elif in_counties:
            county_lines.append(line)
    county_lines.append(']')
    county_data = '\n'.join(county_lines)
    county_data = county_data.replace('\t\t', '\t\t"')
    county_data = county_data.replace(': ', '": ')
    county_df = pd.DataFrame(json.loads(county_data))
    county_df.to_csv('nytimes_us_county_cases.csv', index=False)
    