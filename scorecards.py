import pandas as pd

HARVARD_SCORECARD_REPLACE = {
    'HRR': 'hrr',
    'Adult Population': 'adult_pop',
    'Population 65+': 'senior_pop',
    'Total Hospital Beds': 'total_hosp_beds',
    'Total ICU Beds': 'total_icu_beds',
    'Available Hospital Beds': 'avail_hosp_beds',
    ', ': '_',
    'Six Months': '6mo',
    'Twelve Months': '12mo',
    'Eighteen Months': '18mo'
}

def preprocess_scorecards(scorecards_dir: str,
                          state_code: str = 'MA'):
    """Loads Harvard Global Health scenario scorecards.

    Expected filenames: hrr_scorecard_<percent of population>.csv
    """
    dfs = {}
    for filename in os.listdir(scorecards_dir):
        if filename.startswith('hrr_scorecard_') and filename.endswith('.csv'):
            pop_percent = filename.replace('hrr_scorecard_', '').replace('.csv', '')
            df = pd.read_csv(os.path.join(scorecards_dir, filename))
            state_scorecard = df[df['HRR'].str.contains(f', {state_code}')]
            state_scorecard.reset_index()
            drop_cols = [col for col in state_scorecard.columns
                         if 'Percentage of' in col or 'Potentially' in col]
            state_scorecard = state_scorecard.drop(columns=percentage_columns)