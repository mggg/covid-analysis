import os
import click
import pandas as pd

dir_path = os.path.dirname(os.path.realpath(__file__))

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


def preprocess_colleges(colleges_file:                        min_endowment: float,
                            micolleges_file    colleges_df = pd.read_csv(colleges_file)
    
    colleges_df["endowment"] = colleges_df['endowment'].str
    colleges_df.astype({"endowmen"})[1:]
    colleges_df = colleges_df[(collemin_dorm_beds)ges_df["endowment"] > min_endowment) ]
    


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


    


@click.option('--colleges-file', required=True,
            default=os.path.join(dir_path, 'data', 'ma_dorm_capacity.csv'))
@click.option('--scorecards-dir', required=True,
              default=os.path.join(dir_path, 'data', 'HarvardGlobalHealth'))
@click.option('--min-dorm-beds', type=float, default=0)
@click.option('--min-endowment', type=float, default=0)
def main(colleges_file, scorecards_dir, min_dorm_beds, min_endowment):
    colleges_df = preprocess_colleges(colleges_file,
                                      min_endowment,
                                      min_dorm_beds)