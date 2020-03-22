import pandas as pd

ED_INSTITUTIONS_REPLACE = {
    'Institution Name': 'name',
    'dorm capacity': 'capacity',
    'Street address or post office box': 'address',
    'location of institution': 'city',
    'ZIP code': 'zip_code'
}

def load_ed_institutions(ed_institutions_file: str,
                         min_endowment: float,
                         min_capacity: float):
    """Loads database of Massachusetts educational institutions."""
    df = pd.read_csv(ed_institutions_file).rename(columns=ED_INSTITUTIONS_REPLACE)
    df = df.dropna(subset=['capacity'])
    df["endowment"] = df["endowment"].astype(str).str \
                      .replace('$', '').str.replace(',', '').astype(float)
    df["capacity"] = df["capacity"].astype(str).str \
                     .replace(',', '').astype(int)
    df["enrollment"] = df["enrollment"].astype(str).str \
                     .replace(',', '').astype(int)
    df = df[(df["endowment"] > min_endowment) & (df["capacity"] > min_capacity)]
    return df